import chardet

file_path = "C:/Users/kumakura/Desktop/projects/interview_analyzer_py/interview_analyzer_py_bk_DB処理追加_完成/dist/新しいフォルダー/従業員ID_001_面談シート.csv"

with open(file_path, 'rb') as f:
    raw_data = f.read()
    result = chardet.detect(raw_data)
    print(result)
