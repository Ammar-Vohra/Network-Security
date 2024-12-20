import os
import sys
import mlflow

from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging

from networksecurity.entity.artifact_entity import DataTransformationArtifact, ModelTrainerArtifact, ClassificationMetricArtifact
from networksecurity.entity.config_entity import ModelTrainerConfig

from networksecurity.utils.main_utils.utils import save_object, load_object, load_numpy_array_data, evaluate_models
from networksecurity.utils.ml_utils.model.estimator import NetworkModel
from networksecurity.utils.ml_utils.metric.classification_metric import get_classification_score

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import (
    AdaBoostClassifier,
    GradientBoostingClassifier,
    RandomForestClassifier
)



class ModelTrainer:
    def __init__(self, model_trainer_config: ModelTrainerConfig, data_transformation_artifact: DataTransformationArtifact):
        try:
            self.model_trainer_config = model_trainer_config  
            self.data_transformation_artifact = data_transformation_artifact  
        
        except Exception as e:
            raise NetworkSecurityException(e, sys)
        

    def track_mlflow(self, best_model, classificationmetric):
        with mlflow.start_run():
            f1_score = classificationmetric.f1_score
            precision_score = classificationmetric.precision_score
            recall_score = classificationmetric.recall_score

            mlflow.log_metric("f1_score", f1_score)
            mlflow.log_metric("precision_score", precision_score)
            mlflow.log_metric("recall_score", recall_score)
            mlflow.sklearn.log_model(best_model, "model")


    def train_model(self, X_train, y_train, X_test, y_test):
        try:
            models = {
                "Random Forest": RandomForestClassifier(verbose=1),
                "Decision Tree": DecisionTreeClassifier(),
                "Ada Boost Classifier": AdaBoostClassifier(),
                "Logistic Regression": LogisticRegression(verbose=1),
                "Gradient Boost Classifier": GradientBoostingClassifier(verbose=1)
            }

            params = {
                "Random Forest": {
                    "n_estimators": [8,16,32,64,128,256]
                },


                "Decision Tree": {
                    "criterion": ["gini", "entropy", "log_loss"]
                },

                "Ada Boost Classifier":{
                    "learning_rate": [.1, .01, .05, .001],
                    "n_estimators": [8,16,32,64,128,256]

                },


                "Logistic Regression": {},



                "Gradient Boost Classifier": {
                    "learning_rate": [.1, .01, .05, .001],
                    "subsample": [0.6, 0.7, 0.75, 0.8, 0.85, 0.9],
                    "n_estimators": [8,16,32,64,128,256]

                }

            }


            model_report: dict = evaluate_models(X_train=X_train, y_train=y_train, 
                                                 X_test=X_test, y_test=y_test,
                                                 models=models, params=params)

            ## To get the best model score from dict
            best_model_score = max(sorted(model_report.values()))

            ## To get the best model name from dict
            best_model_name = list(model_report.keys())[
                list(model_report.values()).index(best_model_score)
            ]

            best_model = models[best_model_name]

            y_train_pred = best_model.predict(X_train)
            classification_train_metric = get_classification_score(y_true=y_train, y_pred=y_train_pred)
            ## Tracking experiments with MLFLOW
            self.track_mlflow(best_model, classification_train_metric)

            y_test_pred = best_model.predict(X_test)
            classification_test_metric = get_classification_score(y_true=y_test, y_pred=y_test_pred)
            ## Tracking experiments with MLFLOW
            self.track_mlflow(best_model=best_model, classificationmetric=classification_test_metric)


            preprocessor = load_object(file_path=self.data_transformation_artifact.transformed_object_file_path)
            model_dir = os.path.dirname(self.model_trainer_config.trained_model_file_path)
            os.makedirs(model_dir, exist_ok=True)

            network_model = NetworkModel(preprocessor=preprocessor, model=best_model)
            save_object(file_path=self.model_trainer_config.trained_model_file_path, obj=network_model)


            model_trainer_artifact = ModelTrainerArtifact(
                trained_model_file_path=self.model_trainer_config.trained_model_file_path,
                train_metric_artifact=classification_train_metric,
                test_metric_artifact=classification_test_metric
            )

            return model_trainer_artifact


        except Exception as e:
            raise NetworkSecurityException(e,sys)



        
    
    def initiate_model_trainer(self) -> ModelTrainerArtifact:
        try:
            train_file_path = self.data_transformation_artifact.transformed_train_file_path
            test_file_path = self.data_transformation_artifact.transformed_test_file_path

            ## Loading train and test array
            train_arr = load_numpy_array_data(train_file_path)
            test_arr = load_numpy_array_data(test_file_path)

            x_train, y_train, x_test, y_test = (
                train_arr[:, :-1],
                train_arr[:, -1],
                test_arr[:, :-1],
                test_arr[:, -1],

            )

            model_trainer_artifact = self.train_model(x_train, y_train, x_test, y_test)
            return model_trainer_artifact



        except Exception as e:
            raise NetworkSecurityException(e,sys)