import os
import joblib
import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class ModelService:
    def __init__(self, models_dir="models_rv"):
        self.models_dir = os.path.abspath(models_dir)
        self.hmm_models = {}
        self.rv_models = {}
        self.assets = ["WTI", "BRENT", "HO", "GO"]
        self.strategies = ["Outright", "Spread", "Fly", "ZScoreArb", "Kalman"]
        
    def load_models(self):
        """Loads the HMM Gatekeepers and RV Strategy models."""
        hmm_path = os.path.join(self.models_dir, "PhaseB_HMM_models.joblib")
        
        try:
            if os.path.exists(hmm_path):
                self.hmm_models = joblib.load(hmm_path)
                logger.info(f"Loaded HMM models from {hmm_path}")
            else:
                logger.warning(f"HMM model not found at {hmm_path}. Using mock HMM for testing.")
                self.hmm_models = {}
        except Exception as e:
            logger.error(f"Error loading HMM models: {e}")
            
        # Load RV Models
        loaded_count = 0
        for asset in self.assets:
            for strat in ["Outright", "Spread", "Fly"]:
                for state in [0, 1, 2]:
                    model_name = f"{asset}_{strat}_model_state_{state}.joblib"
                    model_path = os.path.join(self.models_dir, model_name)
                    
                    if os.path.exists(model_path):
                        try:
                            self.rv_models[f"{asset}_{strat}_{state}"] = joblib.load(model_path)
                            loaded_count += 1
                        except Exception as e:
                            logger.error(f"Failed to load {model_name}: {e}")
                            
        logger.info(f"Loaded {loaded_count} RV models successfully.")

    def process_data_and_get_signals(self, df_raw: pd.DataFrame, target_asset: str):
        """
        Takes a DataFrame of raw prices (minimum 61 rows), calculates all features,
        and returns signals for the most recent minute.
        """
        if len(df_raw) < 61:
            return 2, {}, {} # Default fallback
            
        df = df_raw.copy()
        
        # 1. Transform Raw Prices to PCA Features & HMM States for ALL assets
        for asset in self.assets:
            cols = [f'{asset}_c1', f'{asset}_c6', f'{asset}_c12']
            if not all(c in df.columns for c in cols):
                logger.warning(f"Missing raw curve data for {asset}. Filling with 0s.")
                for c in cols: df[c] = 0.0
                
            raw_curves = df[cols].values
            
            if asset in self.hmm_models:
                scaler = self.hmm_models[asset]['scaler']
                pca = self.hmm_models[asset]['pca']
                hmm = self.hmm_models[asset]['model']
                
                scaled_curves = scaler.transform(raw_curves)
                pca_features = pca.transform(scaled_curves)
                
                df[f'{asset}_PC1_Level'] = pca_features[:, 0]
                df[f'{asset}_PC2_Slope'] = pca_features[:, 1]
                df[f'{asset}_PC3_Curvature'] = pca_features[:, 2]
                df[f'{asset}_HMM_State'] = hmm.predict(pca_features)
            else:
                df[f'{asset}_PC1_Level'] = 0.0
                df[f'{asset}_PC2_Slope'] = 0.0
                df[f'{asset}_PC3_Curvature'] = 0.0
                df[f'{asset}_HMM_State'] = 2
                
            df[f'{asset}_PC1_1h_Change'] = df[f'{asset}_PC1_Level'].diff(60)
            df[f'{asset}_PC2_1h_Change'] = df[f'{asset}_PC2_Slope'].diff(60)

        # 2. Calculate Global Structural Divergences
        df['CrossState_Arb_Divergence'] = np.abs(df['WTI_HMM_State'] - df['BRENT_HMM_State'])
        df['CrossState_Crack_Divergence'] = np.abs(df['WTI_HMM_State'] - df['HO_HMM_State'])
        df['CrossState_Distillate_Divergence'] = np.abs(df['HO_HMM_State'] - df['GO_HMM_State'])
        
        # 3. Calculate Mean Reversion (Z-Score of WTI-BRENT spread)
        df['WTI_BRENT_Spread'] = df['WTI_c1'] - df['BRENT_c1']
        df['Spread_Mean'] = df['WTI_BRENT_Spread'].rolling(window=60).mean()
        df['Spread_Std'] = df['WTI_BRENT_Spread'].rolling(window=60).std()
        df['Spread_Std'] = df['Spread_Std'].replace(0, 1.0) # Avoid div by zero
        df['Global_Crude_Z_Score'] = (df['WTI_BRENT_Spread'] - df['Spread_Mean']) / df['Spread_Std']
        df['Global_Crude_Z_Score'].fillna(0, inplace=True)
        
        # 4. Extract the CURRENT minute
        current_minute = df.iloc[-1]
        current_state = int(current_minute[f'{target_asset}_HMM_State'])
        
        # 5. Format features
        model_features = {
            f'{target_asset}_PC1_Level': current_minute[f'{target_asset}_PC1_Level'],
            f'{target_asset}_PC2_Slope': current_minute[f'{target_asset}_PC2_Slope'],
            f'{target_asset}_PC3_Curvature': current_minute[f'{target_asset}_PC3_Curvature'],
            'PC1_1h_Change': current_minute[f'{target_asset}_PC1_1h_Change'],
            'PC2_1h_Change': current_minute[f'{target_asset}_PC2_1h_Change'],
            'CrossState_Arb_Divergence': current_minute['CrossState_Arb_Divergence'],
            'CrossState_Crack_Divergence': current_minute['CrossState_Crack_Divergence'],
            'CrossState_Distillate_Divergence': current_minute['CrossState_Distillate_Divergence'],
            'Global_Crude_Z_Score': current_minute['Global_Crude_Z_Score']
        }
        
        df_input = pd.DataFrame([model_features])
        
        # 6. Generate Portfolio Signals
        signals = {'Outright': 0.0, 'Spread': 0.0, 'Fly': 0.0}
        for strat in signals.keys():
            model_key = f"{target_asset}_{strat}_{current_state}"
            if model_key in self.rv_models:
                model = self.rv_models[model_key]
                predicted_change = model.predict(df_input)[0]
                signals[strat] = 1.0 if predicted_change > 0 else -1.0
                
        # 7. Manual Strategies
        z_score = current_minute['Global_Crude_Z_Score']
        arb_signal = 0.0
        if z_score > 1.0:
            arb_signal = -1.0 if target_asset == "WTI" else (1.0 if target_asset == "BRENT" else 0.0)
        elif z_score < -1.0:
            arb_signal = 1.0 if target_asset == "WTI" else (-1.0 if target_asset == "BRENT" else 0.0)
        signals["ZScoreArb"] = arb_signal
        
        # Kalman
        kalman_price = current_minute.get(f'{target_asset}_Kalman', current_minute[f'{target_asset}_c1'])
        kalman_signal = 0.0
        c1 = current_minute[f'{target_asset}_c1']
        if c1 > kalman_price * 1.0005:
            kalman_signal = 1.0
        elif c1 < kalman_price * 0.9995:
            kalman_signal = -1.0
        signals["Kalman"] = kalman_signal
        
        # Standardize for frontend display
        display_features = model_features.copy()
        display_features["PC1_Level"] = display_features[f'{target_asset}_PC1_Level']
        display_features["PC2_Slope"] = display_features[f'{target_asset}_PC2_Slope']
        display_features["PC3_Curvature"] = display_features[f'{target_asset}_PC3_Curvature']
        
        return current_state, display_features, signals

model_service = ModelService()
