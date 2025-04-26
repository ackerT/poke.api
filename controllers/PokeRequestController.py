import json 
import logging
from fastapi import HTTPException
from models.PokeRequest import PokeRequest
from utils.database import execute_query_json
from utils.AQueue import AQueue 
from utils.ABlob import ABlob




# configurar el logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



async def select_pokemon_request( id: int ):
    try:
        query = "select * from pokequeue.requests where id = ?"
        params = (id,)
        result = await execute_query_json( query , params )
        result_dict = json.loads(result)
        return result_dict
    except Exception as e:
        logger.error( f"Error selecting report request {e}" )
        raise HTTPException( status_code=500 , detail="Internal Server Error" )


async def update_pokemon_request( pokemon_request: PokeRequest) -> dict:
    try:
        query = " exec pokequeue.update_poke_request ?, ?, ? "
        if not pokemon_request.url:
            pokemon_request.url = "";

        params = ( pokemon_request.id, pokemon_request.status, pokemon_request.url  )
        result = await execute_query_json( query , params, True )
        result_dict = json.loads(result)
        return result_dict
    except Exception as e:
        logger.error( f"Error updating report request {e}" )
        raise HTTPException( status_code=500 , detail="Internal Server Error" )

async def insert_poke_request( pokemon_request: PokeRequest) -> dict:
    try:
        query = " exec pokequeue.create_poke_request ?, ? "
        params = ( pokemon_request.pokemon_type,pokemon_request.sample_size, )
        result = await execute_query_json( query , params, True )
        result_dict = json.loads(result)
        await AQueue().insert_message_on_queue( result )
        return result_dict
    except Exception as e:
        logger.error( f"Error inserting report reques {e}" )
        raise HTTPException( status_code=500 , detail="Internal Server Error" )


async def get_all_request() -> dict:
    query = """
        select 
            r.id as ReportId
            , s.description as Status
            , r.type as PokemonType
            , r.url 
            , r.created 
            , r.updated
        from pokequeue.requests r 
        inner join pokequeue.status s 
        on r.id_status = s.id 
    """
    result = await execute_query_json( query  )
    result_dict = json.loads(result)
    blob = ABlob()
    for record in result_dict:
        id = record['ReportId']
        record['url'] = f"{record['url']}?{blob.generate_sas(id)}"
    return result_dict 


async def delete_pokemon_report(report_id: int):
    try:
        # 1) Verificar existencia
        query_check = "SELECT * FROM pokequeue.requests WHERE id = ?"
        params = (report_id,)
        exists = await execute_query_json(query_check, params)
        if not json.loads(exists):
            raise HTTPException(status_code=404, detail="Reporte no encontrado")

        # 2) Borrar blob
        blob = ABlob()
        try:
            blob.delete_blob(report_id)
        except Exception as e:
            logger.warning(f"No se pudo eliminar el blob del reporte {report_id}: {e}")

        # 3) Borrar registro en BD
        query_delete = "DELETE FROM pokequeue.requests WHERE id = ?"
        
        await execute_query_json(query_delete, params, True)

        return {"message": f"Reporte {report_id} eliminado correctamente"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar el reporte {report_id}: {e}")
        raise HTTPException(status_code=500, detail="Error interno al eliminar el reporte")
