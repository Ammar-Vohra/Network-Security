from networksecurity.entity.artifact_entity import DataIngestionArtifact,               DataValidationArtifact
from networksecurity.entity.config_entity import DataValidationConfig
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.utils.main_utils.utils import read_yaml_file, write_yaml_file
from networksecurity.constants.training_pipeline import SCHEMA_FILE_PATH
from networksecurity.logging.logger import logging
from scipy.stats import ks_2samp 
import pandas as pd
import os
import sys


class DataValidation:
    def __init__(self, data_ingestion_artifact: DataIngestionArtifact, data_validation_config: DataValidationConfig):

        try: 
            self.data_ingestion_artifact = data_ingestion_artifact
            self.data_validation_config = data_validation_config
            self._schema_config = read_yaml_file(SCHEMA_FILE_PATH)
    
        except Exception as e:
            raise NetworkSecurityException(e,sys)
        
    
    @staticmethod
    def read_data(file_path) -> pd.DataFrame:
        try:
            return pd.read_csv(file_path)

        except Exception as e:
            raise NetworkSecurityException(e, sys)
        
    
    def validate_columns(self, dataframe: pd.DataFrame) -> bool:
        try:
            number_of_columns = len(self._schema_config)
            logging.info(f"Required number of columns: {number_of_columns}")
            logging.info("DataFrame has columns: {}".format(len(dataframe.columns)))
            
            if len(dataframe.columns) == number_of_columns:
                return True
            return False
   
        except Exception as e:
            raise NetworkSecurityException(e, sys)
        
    
    def detect_data_drift(self, base_df, current_df, threshold=0.05) -> bool:
        try:
            status = True
            report = {}
            for column in base_df.columns:
                d1 = base_df[column]
                d2 = current_df[column]
                is_sample_dist = ks_2samp(d1, d2)

                if threshold < is_sample_dist.pvalue:
                    is_found = False
                else: 
                    is_found = True
                    status = False

                report.update({column: {
                    "p_value": float(is_sample_dist.pvalue),
                    "drift_status": is_found
                }})
            
            drift_report_file_path = self.data_validation_config.drift_report_file_path

            ## create directory
            dir_path = os.path.dirname(drift_report_file_path)
            os.makedirs(dir_path, exist_ok=True)

            write_yaml_file(file_path=drift_report_file_path, content=report)

        except Exception as e:
             raise NetworkSecurityException(e, sys)


      

    def initiate_data_validation(self) -> DataValidationArtifact:
        try:
            train_file_path = self.data_ingestion_artifact.train_file_path
            test_file_path = self.data_ingestion_artifact.test_file_path

            ## read data from train and test files
            train_data = DataValidation.read_data(train_file_path)
            test_data = DataValidation.read_data(test_file_path)

            ## validate number of columns
            status = self.validate_columns(dataframe=train_data)
            if not status:
                error_message = f"Train Dataframe does not contain all columns. \n"

            status = self.validate_columns(dataframe=test_data)
            if not status:
                error_message = f"Test Dataframe does not contain all columns. \n"

            ## check data drift
            status = self.detect_data_drift(base_df = train_data, current_df= test_data)
            dir_name = os.path.dirname(self.data_validation_config.valid_train_file_path)
            os.makedirs(dir_name, exist_ok=True)

            train_data.to_csv(
                self.data_validation_config.valid_train_file_path, header=True, index=False
            )

            test_data.to_csv(
                self.data_validation_config.valid_test_file_path, header=True, index=False
            )


            data_validation_artifact = DataValidationArtifact(
                    validation_status =  status,
                    valid_train_file_path = self.data_ingestion_artifact.train_file_path,
                    valid_test_file_path = self.data_ingestion_artifact.test_file_path,
                    invalid_train_file_path = None,
                    invalid_test_file_path = None,
                    drift_report_file_path = self.data_validation_config.drift_report_file_path
            )


            return data_validation_artifact

        
        except Exception as e:
            raise NetworkSecurityException(e,sys)


        
