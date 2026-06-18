from dataproc_sdk.dataproc_sdk_datiopysparksession.datiopysparksession import DatioPysparkSession
import pandas as pd
import numpy as np
import os
import re
import random
from datetime import datetime, timedelta
import string
from google.colab import drive
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.sql.utils import AnalysisException
from pyspark.sql import types as T
from functools import reduce


class ClaseEngine():
    def __init__(self, OUTPUT_PATH):
        self.dataproc = DatioPysparkSession().get_or_create()
        
        self.OUTPUT_PATH = OUTPUT_PATH
        
        self.ruta1 = '/content/drive/MyDrive/Laboratorios/PySpark/Casos de uso/1. Básico/Caso de Uso 3/2.input/planuno/'
        self.ruta2 = '/content/drive/MyDrive/Laboratorios/PySpark/Casos de uso/1. Básico/Caso de Uso 3/2.input/customers_ba/'
        self.ruta3 = '/content/drive/MyDrive/Laboratorios/PySpark/Casos de uso/1. Básico/Caso de Uso 3/2.input/bajas2021/'

        self.csv_path_pyspark = OUTPUT_PATH + 'cuadrante_planuno/'

    def read_data(self):
        self.df_plauno = self.dataproc.read().parquet(self.ruta1)
        self.df_customers = self.dataproc.read().parquet(self.ruta2)
        self.df_bajas = self.dataproc.read().parquet(self.ruta3)

        self.planuno_2020 = self.df_plauno.filter(f.col("date_alta") < "2021-01-01")
        self.planuno_2021 = self.df_plauno.filter(f.col("date_alta") >= "2021-01-01")
    
    def get_base(self):
        df_plauno = self.df_plauno

        self.base = (df_plauno
            .filter((F.col("business_area_id") == "BA03") & (F.col("planuno_quadrant_name") == "Básico"))
            .select("customer_id").distinct()
        )

    def get_antiguedad(self):
        base = self.base
        df_customers = self.df_customers

        self.df_antiguedad = (base
            .join(df_customers.select("customer_id",
                                      F.col("cust_entry_date").alias("fecha_alta_cliente")),
                  "customer_id", "left")
            .withColumn("hoy", F.lit("2022-01-30"))
            .withColumn("diferencia_dias",
                        F.datediff(F.col("hoy").cast("date"),
                                 F.col("fecha_alta_cliente").cast("date")))
            .withColumn(
                "antiguedad",
                when(F.col("diferencia_dias") < 183, "< 6 meses")
                .when(F.col("diferencia_dias") < 365, "6-12 meses")
                .when(F.col("diferencia_dias") < 730, "1-2 años")
                .when(F.col("diferencia_dias") < 1825, "2-5 años")
                .otherwise("> 5 años")
            )
        )

    def get_refundidos(self):
        planuno_2020 = self.planuno_2020
        w = Window.partitionBy("customer_id").orderBy(F.col("date_alta").desc())

        self.refunidos_df = (planuno_2020
            .withColumn("row_number", F.row_number().over(w))
            .filter(F.col("row_number") == 1)
            .drop("row_number")
            .select("customer_id", "date_alta"))

    def get_clasificacion(self):
        planuno_2020 = self.planuno_2020

        self.planuno_2021_enriq = (planuno_2020
            .withColumn(
                "Exclusivos_3d3",
                F.when(
                    (
                      (F.col("customer_type").isin(
                          "B.PRIVADA", "B.PERSONAL", "PARTICULARES", "PAES")) &
                      (F.col("mobile_digital_crit_type") == 1) &
                      (F.col("income_freelance_type") == 0) &
                      (F.col("transac_business_type") == 0)
                    ) |
                    (
                      (F.col("customer_type") == "PYMES") &
                      (F.col("mobile_digital_crit_type") == 1) &
                      (F.expr("soc_insur_asgn_fulflt_type  + payroll_asgn_crit_type + tax_pymt_crit_type") == 1) &
                      (F.col("planuno_segment_id").isin("PT","AT","CT","BT","VT"))
                    ),
                    F.lit("Exclusivos_3d3")
                ).otherwise("Otros")
            )
            .select("customer_id", "planuno_quadrant_name", "Exclusivos_3d3"))

    def get_union(self):
        df_antiguedad = self.df_antiguedad
        planuno_2021_enriq = self.planuno_2021_enriq
        df_bajas = self.df_bajas

        self.df = (df_antiguedad.join(planuno_2021_enriq, "customer_id", "left")
            .join(df_bajas.select("customer_id", F.col("movement_type")), "customer_id", "left")
            .withColumn("bajas", F.when(F.col("movement_type") == "baja", 1).otherwise(0))
        )

    def get_cuadrante(self):
        df = self.df
        
        self.df_cuadrante_planuno = (df
            .withColumn(
                "cuadrante_planuno",
                F.when(F.col("bajas") == 1, "BAJAS")
                .when(
                    (F.col("planuno_quadrant_name") == "Transaccional") &
                    (F.col("Exclusivos_3d3") == "Exclusivos_3d3"),
                    "3d3"
                )
                .otherwise(F.col("planuno_quadrant_name"))
            )
        )

    def to_csv(self):
        self.dataproc.write() \
            .option("partitionOverwriteMode", "dynamic") \
            .mode("overwrite") \
            .parquet(self.df_cuadrante_planuno.coalesce(1), self.csv_path_pyspark)

    def run(self):
        self.read_data()
        self.get_base()
        self.get_antiguedad()
        self.get_refundidos()
        self.get_clasificacion()
        self.get_union()
        self.get_cuadrante()
        self.to_csv()