import pytest
from pyspark.sql import SparkSession 
from pyspark.sql import functions as F 
from basicengine.utils.funciones import ClaseEngine

@pytest.fixture(scope="session") 
def spark(): 
    return SparkSession.builder.master("local[1]").appName("unit-tests").getOrCreate()

def test_example(spark):
    assert True==True

# def test_obtain_carterizados_basic(spark): 

#     # --- Input DataFrames simulados --- 
#     ncm_data = [ 
#         ("0182", "ES", 1, "CUST01", " usr1 ", " mat01 "), 
#         ("0182", "ES", 2, "CUST02", "usr2", "mat02"),  # debería ser filtrado 
#     ] 

#     uge_data = [ 
#         ("0182", " 1 ", "usr1", "BR01", "POS01", "Juan", "Pérez", "López", "usr1"), 
#         ("0182", "0", "usr3", "BR02", "POS02", "Ana", "García", "Martín", "usr3"),  # empleado_id = 0 
#     ] 

#     ncm = spark.createDataFrame(ncm_data, ["entity_id", "crm_country_id", "bw_rel_type", 
#                                            "customer_id", "incl_external_manager_id", "rating_enrol_manager_id"]) 
#     uge = spark.createDataFrame(uge_data, ["entity_id", "employee_id", "user_id", "branch_id", "position_id", 
#                                            "user_name", "employee_first_last_name", "employee_second_last_name", "usuario"]) 

#     # --- Ejecutar función --- 
#     result = obtain_carterizados(ncm, uge) 

#     # --- Validaciones --- 
#     result_data = result.collect() 
#     assert len(result_data) == 1  # solo una combinación válida 
#     row = result_data[0] 
#     assert row.gf_customer_id == "CUST01" 
#     assert row.nombre_gestor == "Juan" 
#     assert row.oficina_gestor == "BR01" 
#     assert row.matricula_gestor == "mat01".strip() 