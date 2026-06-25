from typing import Dict 
from colab_funciones_example import ClaseEngine
from google.colab import drive


class DataprocExperiment:
    """
    Just a wrapper class to ease the user code execution.
    """ 

    def __init__(self): 
        """ 
        Constructor 
        """ 
        # self.logger = get_user_logger(DataprocExperiment.__qualname__) 
    
    def run(self, **parameters: Dict) -> None: 
        """ 
        Execute the code written by the user. 
    
        Args: 
            parameters: The config file parameters 
        """ 
    
        #  Parameters 
        OUTPUT_PATH = str(parameters["OUTPUT_PATH"])

        try:
            engine = ClaseEngine(OUTPUT_PATH)
            engine.run()
        except Exception as e:
            print(f"ERROR: {e}")
        finally:
            print('Final proceso')

if __name__ == "__main__":
    # drive.mount('/content/drive')
    exp = DataprocExperiment()
    conf = {"OUTPUT_PATH": '/content/drive/MyDrive/1. Básico/Caso de Uso 3/4.output/'}
    exp.run(**conf)