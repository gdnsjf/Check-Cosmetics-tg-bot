import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, precision_score, recall_score, f1_score, confusion_matrix
import joblib
import seaborn as sns
import matplotlib.pyplot as plt
from imblearn.over_sampling import SMOTE

# Функция токенизации ингредиентов
def custom_tokenizer(text):
    return text.split(",")

# Загрузка данных
def load_data(file_path):
    df = pd.read_csv(file_path)
    return df

# Очистка данных
def clean_data(df):
    df = df.dropna(subset=['Ingredient', 'EWG Rating']) # Удаляет строки с пропущенными значениями в столбцах "Ingredient" и "EWG Rating".
    df = df[df['Ingredient'].str.strip() != '']
    df['EWG Rating'] = pd.to_numeric(df['EWG Rating'], errors='coerce') # Преобразует значения EWG Rating в числовой формат
    return df

# Предобработка данных
def preprocess_data(df):
    vectorizer = TfidfVectorizer(tokenizer=custom_tokenizer)
    X = vectorizer.fit_transform(df['Ingredient'])

    # Преобразуем 'EWG Rating' в категории 0, 1, 2
    df['EWG Rating'] = pd.cut(df['EWG Rating'], bins=[-1, 2, 6, 10], labels=[0, 1, 2]).astype(int)

    y = df['EWG Rating']

    if X.shape[0] != y.shape[0]:
        raise ValueError("Mismatch between number of samples in X and y")

    # Применение SMOTE для балансировки классов
    smote = SMOTE(random_state=42)
    X_resampled, y_resampled = smote.fit_resample(X, y)

    return X_resampled, y_resampled, vectorizer

# Обучение модели
def train_model(X_train, y_train, n_estimators=300):
    model = RandomForestClassifier(n_estimators=n_estimators, random_state=42, class_weight='balanced')
    model.fit(X_train, y_train)
    return model
# Оценка модели
def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)

    # Метрики
    accuracy = model.score(X_test, y_test)
    precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)

    print(f'Accuracy: {accuracy}')
    print(f'Precision: {precision}')
    print(f'Recall: {recall}')
    print(f'F1-Score: {f1}')

    # Classification Report
    report = classification_report(y_test, y_pred, zero_division=0)
    print(report)

# Сохранение модели и векторизатора
def save_model(model, vectorizer, model_path='cosmetic_safety_model.pkl', vectorizer_path='vectorizer.pkl'):
    joblib.dump(model, model_path)
    joblib.dump(vectorizer, vectorizer_path)

def main():
    # Загрузка данных
    file_path = 'C:/Users/Настюша/PycharmProjects/pythonProject10/ingredients.csv'
    df = load_data(file_path)

    # Очистка и предобработка данных
    df = clean_data(df)
    X, y, vectorizer = preprocess_data(df)

    # Разделение на тренировочные и тестовые данные
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Обучение модели с 300 деревьями
    model = train_model(X_train, y_train, n_estimators=300)

    # Оценка модели
    evaluate_model(model, X_test, y_test)

    # Сохранение модели и векторизатора
    save_model(model, vectorizer)

if __name__ == "__main__":
    main()