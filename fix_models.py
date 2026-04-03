import joblib

# Diabetes
model = joblib.load("models/diabetes_xgboost_final.pkl")
joblib.dump(model, "models/diabetes_xgboost_final.pkl", compress=3)

scaler = joblib.load("models/diabetes_scaler.pkl")
joblib.dump(scaler, "models/diabetes_scaler.pkl", compress=3)

# Heart
model = joblib.load("models/heart_xgboost_final.pkl")
joblib.dump(model, "models/heart_xgboost_final.pkl", compress=3)

scaler = joblib.load("models/heart_scaler.pkl")
joblib.dump(scaler, "models/heart_scaler.pkl", compress=3)

# Kidney
model = joblib.load("models/kidney_xgboost_final.pkl")
joblib.dump(model, "models/kidney_xgboost_final.pkl", compress=3)

scaler = joblib.load("models/kidney_scaler.pkl")
joblib.dump(scaler, "models/kidney_scaler.pkl", compress=3)

print("✅ Models re-saved successfully")