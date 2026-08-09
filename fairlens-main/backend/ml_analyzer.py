import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import shap

class BiasAnalyzer:
    def __init__(self):
        self.model = LogisticRegression(max_iter=1000)
        self.label_encoders = {}
        self.feature_columns = ['gender', 'college_tier', 'skills_score', 'projects', 'test_score']
        self.target_column = 'decision'
        self.sensitive_attributes = ['gender', 'college_tier']
        
    def _preprocess(self, df):
        df_encoded = df.copy()
        
        # Ensure correct types
        for col in ['skills_score', 'test_score']:
            if col in df_encoded.columns:
                df_encoded[col] = pd.to_numeric(df_encoded[col], errors='coerce').fillna(0)
                
        for col in ['projects']:
            if col in df_encoded.columns:
                df_encoded[col] = pd.to_numeric(df_encoded[col], errors='coerce').fillna(0).astype(int)

        # Encode categorical columns
        for col in self.feature_columns:
            if not pd.api.types.is_numeric_dtype(df_encoded[col]):
                le = LabelEncoder()
                df_encoded[col] = le.fit_transform(df_encoded[col].astype(str))
                self.label_encoders[col] = le
                
        if self.target_column in df_encoded.columns:
            le_target = LabelEncoder()
            df_encoded[self.target_column] = le_target.fit_transform(df_encoded[self.target_column].astype(str))
            # Keep track so 1=Selected, 0=Rejected (assuming alphabetical formatting, we will explicitly check)
            self.label_encoders[self.target_column] = le_target
            
        return df_encoded

    def _get_target_mapping(self):
        # We want 'Selected' to be 1 and 'Rejected' to be 0
        if self.target_column in self.label_encoders:
            classes = list(self.label_encoders[self.target_column].classes_)
            # Map original names back to integer values
            mapping = {name: int(val) for val, name in zip(self.label_encoders[self.target_column].transform(classes), classes)}
            selected_class = mapping.get("Selected", 1)  # Default fallback
            return selected_class
        return 1

    def train_and_evaluate(self, df):
        if self.is_trained:
           return self.accuracy, df, df

    df_clean = df.dropna(subset=self.feature_columns + [self.target_column])
    df_encoded = self._preprocess(df_clean)
    
    X = df_encoded[self.feature_columns]
    y = df_encoded[self.target_column]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    self.model.fit(X_train, y_train)
    
    y_pred = self.model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    self.is_trained = True
    self.accuracy = acc

    return acc, df_clean, df_encoded 

    def calculate_fairness_metrics(self, df):
        """ Calculate Demographic Parity and Disparate Impact """
        df_encoded = self._preprocess(df)
        X = df_encoded[self.feature_columns]
        
        # Predict on entire dataset
        predictions = self.model.predict(X)
        df['predicted_decision_num'] = predictions
        
        selected_target_val = self._get_target_mapping()
        df['is_selected'] = (df['predicted_decision_num'] == selected_target_val).astype(int)
        
        metrics = {}
        for sensitive_attr in self.sensitive_attributes:
            groups = df[sensitive_attr].unique()
            selection_rates = {}
            for group in groups:
                group_data = df[df[sensitive_attr] == group]
                rate = group_data['is_selected'].mean() if len(group_data) > 0 else 0
                selection_rates[str(group)] = rate
            
            # Demographic parity diff (max rate - min rate)
            rates = list(selection_rates.values())
            dp = max(rates) - min(rates) if rates else 0
            
            # Disparate Impact (min rate / max rate)
            di = min(rates) / max(rates) if max(rates) > 0 else 0
            
            metrics[sensitive_attr] = {
                'selection_rates': selection_rates,
                'demographic_parity': dp,
                'disparate_impact': di
            }
            
        return metrics

    def generate_counterfactuals(self, df, num_cases=10):
        """ Find instances where flipping a sensitive attribute changes the outcome """
        df_encoded = self._preprocess(df)
        X = df_encoded[self.feature_columns]
        
        original_preds = self.model.predict(X)
        
        counterfactuals = []
        
        # Test flipping gender
        if 'gender' in self.label_encoders:
            gender_le = self.label_encoders['gender']
            genders = gender_le.classes_
            
            for idx in range(min(500, len(X))): # Scan first 500 records
                orig_gender_num = X.iloc[idx]['gender']
                orig_gender_str = gender_le.inverse_transform([int(orig_gender_num)])[0]
                
                for other_gender in genders:
                    if other_gender != orig_gender_str:
                        other_gender_num = gender_le.transform([other_gender])[0]
                        X_cf = X.iloc[idx:idx+1].copy()
                        X_cf['gender'] = other_gender_num
                        
                        new_pred = self.model.predict(X_cf)[0]
                        
                        if new_pred != original_preds[idx]:
                            # Flipped!
                            person = df.iloc[idx]
                            
                            target_le = self.label_encoders.get(self.target_column)
                            orig_pred_str = target_le.inverse_transform([original_preds[idx]])[0] if target_le else original_preds[idx]
                            new_pred_str = target_le.inverse_transform([new_pred])[0] if target_le else new_pred
                            
                            counterfactuals.append({
                                'name': person.get('name', f"Candidate #{idx}"),
                                'attribute': 'gender',
                                'original_value': orig_gender_str,
                                'flipped_value': other_gender,
                                'original_decision': orig_pred_str,
                                'new_decision': new_pred_str
                            })
                            if len(counterfactuals) >= num_cases:
                                break
                if len(counterfactuals) >= num_cases:
                    break

        return counterfactuals

    def compute_feature_importance(self, df):
        """ Using SHAP for Explainability """
        df_encoded = self._preprocess(df)
        X = df_encoded[self.feature_columns]
        
        explainer = shap.LinearExplainer(self.model, X)
        shap_values = explainer.shap_values(X)
        
        # Mean absolute SHAP value for each feature
        if isinstance(shap_values, list): # For multi-class (shouldn't happen with Binary LR)
            mean_shap = np.abs(shap_values[1]).mean(axis=0)
        else:
            mean_shap = np.abs(shap_values).mean(axis=0)
            
        importance = {feature: float(val) for feature, val in zip(self.feature_columns, mean_shap)}
        # Normalize
        total = sum(importance.values())
        if total > 0:
            importance = {k: v/total for k, v in importance.items()}
            
        return importance
        
    def get_recommendations(self, fairness_metrics):
        recs = []
        overall_bias_score = 0
        
        for attr, vals in fairness_metrics.items():
            di = vals['disparate_impact']
            dp = vals['demographic_parity']
            
            # Map the overall bias score directly to the percentage gap
            current_bias_percent = dp * 100
            if current_bias_percent > overall_bias_score:
                overall_bias_score = current_bias_percent
            
            if di < 0.8: # Four-Fifths rule
                recs.append(f"Severe bias detected in {attr} (Disparate Impact = {di:.2f} < 0.8). Consider removing this feature or applying bias mitigation techniques.")
            elif di < 0.9:
                recs.append(f"Moderate bias in {attr} (Disparate Impact = {di:.2f}). Monitor selection rates across groups.")
                
            if dp > 0.15:
                recs.append(f"High Demographic Parity difference ({dp:.2f}) observed in {attr}. Ensure your training dataset is balanced.")
                
        overall_bias_score = min(100, max(0, overall_bias_score))
        
        if overall_bias_score < 3:
            recs.append("Model appears to be perfectly fair across measured sensitive attributes.")
        elif len(recs) == 0:
            recs.append(f"Model exhibits very slight bias ({overall_bias_score:.1f}% shift). Monitor acceptable thresholds.")
            
        return overall_bias_score, recs

    def run_audit(self, df):
        acc, df_clean, df_encoded = self.train_and_evaluate(df)
        fairness = self.calculate_fairness_metrics(df_clean)
        cf = self.generate_counterfactuals(df_clean)
        importance = self.compute_feature_importance(df_clean)
        score, recs = self.get_recommendations(fairness)
        
        return {
            "accuracy": float(acc),
            "bias_score": float(score),
            "fairness_metrics": fairness,
            "feature_importance": importance,
            "counterfactuals": cf,
            "recommendations": recs
        }
