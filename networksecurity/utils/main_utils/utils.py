import yaml
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
import os, sys
import numpy as np
import pickle
import dill
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import r2_score


def read_yaml_file(file_path: str) -> dict:
    try:
        with open(file_path, "rb") as yaml_file:
            return yaml.safe_load(yaml_file)


    except Exception as e:
        raise NetworkSecurityException(e,sys)
    

def write_yaml_file(file_path: str, content: object, replace: bool = False) ->None:
    try:
        if replace:
            if os.path.exists(file_path):
                os.remove(file_path)

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "w") as file:
            yaml.dump(content, file)

    except Exception as e:
        raise NetworkSecurityException(e, sys)
    


def save_numpy_array(file_path: str, array: np.array):
    try:
        dir_path = os.path.dirname(file_path)
        os.makedirs(dir_path, exist_ok= True)
        with open(file_path, "wb") as file:
            np.save(file, array)

    except Exception as e:
        raise NetworkSecurityException(e,sys)
    

def save_object(file_path: str, obj: object ) -> None:
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as file:
            pickle.dump(obj, file)

    except Exception as e:
        raise NetworkSecurityException(e,sys)



def load_object(file_path: str) -> object:
    try:
        if not os.path.exists(file_path):
            raise Exception(f"The file: {file_path} does not exist")

        with open(file_path, "rb") as file_obj:
            print(file_obj)
            return pickle.load(file_obj)

    except Exception as e:
        raise NetworkSecurityException(e, sys)




def load_numpy_array_data(file_path: str) -> np.array:
    try: 
        with open(file_path, "rb") as file_obj:
            return np.load(file_obj)

    except Exception as e:
        raise NetworkSecurityException(e, sys)



def evaluate_models(X_train, y_train, X_test, y_test, models, params):
    try:
        report = {}

        # Iterate through each model
        for model_name, model in models.items():
            para = params.get(model_name, {})  # Retrieve parameters for the current model

            # Perform GridSearchCV
            gs = GridSearchCV(model, para, cv=3)
            gs.fit(X_train, y_train)

            # Update model with best parameters
            model.set_params(**gs.best_params_)
            model.fit(X_train, y_train)

            # Generate predictions
            y_train_pred = model.predict(X_train)
            y_test_pred = model.predict(X_test)

            # Calculate model performance scores
            train_model_score = r2_score(y_train, y_train_pred)
            test_model_score = r2_score(y_test, y_test_pred)

            # Log test model score in the report
            report[model_name] = test_model_score

        return report  # Return the complete report after all models are evaluated

    except Exception as e:
        raise NetworkSecurityException(e, sys)
