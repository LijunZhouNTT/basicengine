import pytest
from pyspark.sql import SparkSession 
from pyspark.sql import functions as F 
from basicengine.utils.funciones import ClaseEngine

@pytest.fixture(scope="session") 
def spark(): 
    return SparkSession.builder.master("local[1]").appName("unit-tests").getOrCreate()

def test_get_base(spark):
    engine = ClaseEngine("/tmp/")

    engine.df_plauno = spark.createDataFrame([
        ("BA03", "Básico", 1),
        ("BA03", "Premium", 2),
        ("BA01", "Básico", 3)
    ], ["business_area_id", "planuno_quadrant_name", "customer_id"])

    engine.get_base()

    result = [row.customer_id for row in engine.base.collect()]

    assert result == [1]

def test_get_antiguedad(spark):
    engine = ClaseEngine("/tmp/")

    # base
    engine.base = spark.createDataFrame([
        (1,),
        (2,)
    ], ["customer_id"])

    # customers
    engine.df_customers = spark.createDataFrame([
        (1, "2023-01-01"),  # cliente reciente
        (2, "2015-01-01")   # cliente antiguo
    ], ["customer_id", "cust_entry_date"])

    engine.get_antiguedad()

    result = engine.df_antiguedad.select("customer_id", "antiguedad").collect()

    res_dict = {r.customer_id: r.antiguedad for r in result}

    assert res_dict[1] == "< 6 meses"
    assert res_dict[2] == "> 5 años"

def test_get_refundidos(spark):
    engine = ClaseEngine("/tmp/")

    engine.planuno_2020 = spark.createDataFrame([
        (1, "2020-01-01"),
        (1, "2020-06-01"),  # más reciente
        (2, "2020-03-01")
    ], ["customer_id", "date_alta"])

    engine.get_refundidos()

    result = engine.refunidos_df.collect()
    res = {r.customer_id: r.date_alta for r in result}

    assert res[1] == "2020-06-01"
    assert res[2] == "2020-03-01"

def test_get_clasificacion(spark):
    engine = ClaseEngine("/tmp/")

    engine.planuno_2020 = spark.createDataFrame([
        ("1", "B.PERSONAL", 1, 0, 0, 1, 0, 0, "X", "Transaccional"),
        ("2", "PYMES", 1, 0, 0, 0, 0, 0, "ZZ", "Básico"),
        ("3", "PYMES", 1, 1, 0, 0, 1, 0, "PT", "Transaccional")
    ], [
        "customer_id",
        "customer_type",
        "mobile_digital_crit_type",
        "income_freelance_type",
        "transac_business_type",
        "soc_insur_asgn_fulflt_type",
        "payroll_asgn_crit_type",
        "tax_pymt_crit_type",
        "planuno_segment_id",
        "planuno_quadrant_name"
    ])

    engine.get_clasificacion()

    df = engine.planuno_2021_enriq.collect()
    res = {r.customer_id: r.Exclusivos_3d3 for r in df}

    assert res["1"] == "Exclusivos_3d3"
    assert res["2"] == "Otros"
    assert res["3"] == "Exclusivos_3d3"

def test_get_union(spark):
    engine = ClaseEngine("/tmp/")

    engine.df_antiguedad = spark.createDataFrame([
        (1, "6-12 meses"),
        (2, "1-2 años")
    ], ["customer_id", "antiguedad"])

    engine.planuno_2021_enriq = spark.createDataFrame([
        (1, "Transaccional", "Exclusivos_3d3"),
        (2, "Básico", "Otros")
    ], ["customer_id", "planuno_quadrant_name", "Exclusivos_3d3"])

    engine.df_bajas = spark.createDataFrame([
        (1, "baja"),
        (2, "activo")
    ], ["customer_id", "movement_type"])

    engine.get_union()

    df = engine.df.collect()
    res = {r.customer_id: (r.bajas, r.movement_type) for r in df}

    assert res[1][0] == 1
    assert res[2][0] == 0

def test_get_cuadrante(spark):
    engine = ClaseEngine("/tmp/")

    engine.df = spark.createDataFrame([
        # baja
        (1, "Transaccional", "Exclusivos_3d3", 1),

        # caso 3d3
        (2, "Transaccional", "Exclusivos_3d3", 0),

        # default
        (3, "Básico", "Otros", 0)
    ], [
        "customer_id",
        "planuno_quadrant_name",
        "Exclusivos_3d3",
        "bajas"
    ])

    engine.get_cuadrante()

    df = engine.df_cuadrante_planuno.collect()
    res = {r.customer_id: r.cuadrante_planuno for r in df}

    assert res[1] == "BAJAS"
    assert res[2] == "3d3"
    assert res[3] == "Básico"