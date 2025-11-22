#!/usr/bin/env python3
"""
ML Model Training Runner
Trains a simple ML model for predicting stock movements
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import warnings
warnings.filterwarnings('ignore')

def train_ml_model():
    """Train a simple ML model for stock prediction"""

    print("\n" + "="*70)
    print("ML MODEL TRAINING - STOCK MOVEMENT PREDICTOR")
    print("="*70)

    # Symbols to train on
    symbols = ['TCS.NS', 'RELIANCE.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS']

    print(f"Training on: {', '.join([s.replace('.NS', '') for s in symbols])}")
    print("Model: Random Forest Classifier")
    print("Target: Predict if stock will go up >2% in next 5 days")
    print("-"*70)

    all_features = []
    all_labels = []

    for symbol in symbols:
        try:
            print(f"\nProcessing {symbol}...")

            # Fetch 1 year of data
            stock = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            df = stock.history(start=start_date, end=end_date)

            if df.empty or len(df) < 50:
                print(f"  ⚠️  Insufficient data for {symbol}")
                continue

            # Feature engineering
            df['Returns_1d'] = df['Close'].pct_change()
            df['Returns_5d'] = df['Close'].pct_change(5)
            df['Returns_20d'] = df['Close'].pct_change(20)
            df['Volume_Ratio'] = df['Volume'] / df['Volume'].rolling(20).mean()
            df['High_Low_Ratio'] = (df['High'] - df['Low']) / df['Close']
            df['Close_Open_Ratio'] = (df['Close'] - df['Open']) / df['Open']

            # Technical indicators
            df['MA_20'] = df['Close'].rolling(20).mean()
            df['MA_50'] = df['Close'].rolling(50).mean()
            df['MA_Ratio'] = df['MA_20'] / df['MA_50']
            df['Price_MA20_Ratio'] = df['Close'] / df['MA_20']

            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # Volatility
            df['Volatility'] = df['Returns_1d'].rolling(20).std()

            # Target: Will stock go up >2% in next 5 days?
            df['Future_Return'] = df['Close'].shift(-5) / df['Close'] - 1
            df['Target'] = (df['Future_Return'] > 0.02).astype(int)

            # Features for ML
            feature_cols = ['Returns_1d', 'Returns_5d', 'Returns_20d', 'Volume_Ratio',
                          'High_Low_Ratio', 'Close_Open_Ratio', 'MA_Ratio',
                          'Price_MA20_Ratio', 'RSI', 'Volatility']

            # Drop NaN values
            df_clean = df[feature_cols + ['Target']].dropna()

            if len(df_clean) > 30:
                features = df_clean[feature_cols].values
                labels = df_clean['Target'].values

                all_features.append(features)
                all_labels.append(labels)

                print(f"  ✅ Added {len(features)} samples")

        except Exception as e:
            print(f"  ❌ Error: {e}")

    # Combine all data
    if all_features:
        X = np.vstack(all_features)
        y = np.hstack(all_labels)

        print("\n" + "-"*70)
        print(f"Total samples: {len(X)}")
        print(f"Features: {len(X[0])}")
        print(f"Positive samples (up >2%): {sum(y)} ({sum(y)/len(y)*100:.1f}%)")
        print(f"Negative samples: {len(y)-sum(y)} ({(len(y)-sum(y))/len(y)*100:.1f}%)")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        print("\n" + "-"*70)
        print("Training Random Forest model...")

        # Train model
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=20,
            random_state=42
        )

        model.fit(X_train, y_train)

        # Evaluate
        train_score = model.score(X_train, y_train)
        test_score = model.score(X_test, y_test)

        y_pred = model.predict(X_test)

        print(f"\n📊 Model Performance:")
        print(f"  • Training Accuracy: {train_score*100:.1f}%")
        print(f"  • Testing Accuracy: {test_score*100:.1f}%")

        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': ['Returns_1d', 'Returns_5d', 'Returns_20d', 'Volume_Ratio',
                       'High_Low_Ratio', 'Close_Open_Ratio', 'MA_Ratio',
                       'Price_MA20_Ratio', 'RSI', 'Volatility'],
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)

        print(f"\n🔍 Top 5 Important Features:")
        for idx, row in feature_importance.head(5).iterrows():
            print(f"  • {row['feature']}: {row['importance']*100:.1f}%")

        # Classification report
        print(f"\n📈 Classification Report:")
        print(classification_report(y_test, y_pred,
                                   target_names=['Hold/Sell', 'Buy (>2%)'],
                                   labels=[0, 1]))

        # Recent predictions
        print("\n🔮 Sample Predictions on Test Set:")
        sample_indices = np.random.choice(len(X_test), 5, replace=False)
        for i in sample_indices:
            pred = model.predict_proba([X_test[i]])[0]
            actual = y_test[i]
            print(f"  • Prediction: {'BUY' if pred[1] > 0.5 else 'HOLD'} "
                  f"(confidence: {max(pred)*100:.1f}%) | "
                  f"Actual: {'UP >2%' if actual == 1 else 'FLAT/DOWN'}")

        print("\n" + "="*70)
        print("Model training complete!")
        print("="*70)

        return model

    else:
        print("\n❌ No data available for training")
        return None

if __name__ == "__main__":
    model = train_ml_model()