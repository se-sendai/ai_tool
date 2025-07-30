# エラーハンドリングの粒度 修正方針

`code_review_notes.md`の指摘に基づき、`backend_logic.py`の`call_ai_model`関数におけるエラーハンドリングの粒度を改善し、より具体的な例外を個別にキャッチするように修正します。これにより、デバッグの容易性とエラー発生時の原因特定を向上させます。

## 現状の課題

`call_ai_model`関数では、AIモデルの呼び出し時に発生する様々なエラーを`Exception as e`という広範な例外で一括してキャッチしています。これでは、ネットワークエラー、APIからの不正な応答、JSONパースエラーなど、具体的なエラーの種類を判別することが困難です。

## 修正方針

1.  **具体的な例外の特定**: `call_ai_model`関数内で発生しうる具体的な例外を特定します。
    *   `requests.exceptions.Timeout`: ネットワークリクエストのタイムアウト
    *   `requests.exceptions.RequestException`: その他のrequestsライブラリ起因のネットワークエラー（接続エラー、HTTPエラーなど）
    *   `json.JSONDecodeError`: AIからの応答が不正なJSON形式であった場合
    *   `genai.core.exceptions.GoogleGenerativeAIException`: Gemini API固有のエラー（APIキー無効、レート制限など）
    *   その他の予期せぬエラー

2.  **個別キャッチと適切な処理**: 特定した例外ごとに`try-except`ブロックを設け、それぞれに応じたエラーメッセージのロギングや、必要に応じた再試行ロジックの調整を行います。

3.  **フォールバック**: 上記の具体的な例外でキャッチできなかったエラーについては、引き続き汎用的な`Exception`でキャッチし、予期せぬ問題に対応します。

## 修正箇所 (予測)

### `src/backend_logic.py` の `call_ai_model` 関数

**修正前 (抜粋):**

```python
def call_ai_model(prompt, model_type="generative"):
    """AIバックエンドに応じてモデルを呼び出す共通関数"""
    for attempt in range(MAX_RETRIES):
        try:
            # ... AI呼び出しロジック ...
        except requests.exceptions.Timeout:
            logging.warning(f"AI API呼び出しがタイムアウトしました (試行 {attempt + 1}/{MAX_RETRIES})。再試行します...")
        except requests.exceptions.RequestException as e:
            logging.warning(f"AI API呼び出し中にエラーが発生しました: {e} (試行 {attempt + 1}/{MAX_RETRIES})。再試行します...")
        except Exception as e: # ← この部分をより具体的にする
            logging.error(f"予期せぬエラーが発生しました: {e} (試行 {attempt + 1}/{MAX_RETRIES})。再試行します...")
        
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY_SECONDS)
    
    logging.error(f"AI API呼び出しが{MAX_RETRIES}回試行されましたが、すべて失敗しました。")
    return None
```

**修正後 (予測):**

```python
import google.generativeai.types as genai_types # 追加

def call_ai_model(prompt, model_type="generative"):
    """AIバックエンドに応じてモデルを呼び出す共通関数"""
    for attempt in range(MAX_RETRIES):
        try:
            if AI_BACKEND == ConfigKeys.GEMINI:
                # ... Gemini API呼び出しロジック ...
                response = model.generate_content(prompt, request_options={'timeout': 60})
                # ... 応答処理 ...
            elif AI_BACKEND == ConfigKeys.OLLAMA:
                # ... Ollama API呼び出しロジック ...
                response = requests.post(f"{OLLAMA_URL}/api/generate", headers=headers, json=data, timeout=60)
                response.raise_for_status()
                # ... 応答処理 ...

        except requests.exceptions.Timeout as e:
            logging.warning(f"AI API呼び出しがタイムアウトしました: {e} (試行 {attempt + 1}/{MAX_RETRIES})。再試行します...")
        except requests.exceptions.RequestException as e:
            logging.warning(f"AI API呼び出し中にネットワークエラーが発生しました: {e} (試行 {attempt + 1}/{MAX_RETRIES})。再試行します...")
        except json.JSONDecodeError as e:
            logging.error(f"AIからの応答が不正なJSON形式でした: {e} (試行 {attempt + 1}/{MAX_RETRIES})。再試行しません。")
            return None # JSONパースエラーは再試行しても解決しない可能性が高いため、即座に終了
        except genai_types.BlockedPromptException as e: # Gemini固有の例外
            logging.error(f"不適切なプロンプトによりAIの応答がブロックされました: {e}")
            return None
        except genai_types.BlockedMimeTypeException as e: # Gemini固有の例外
            logging.error(f"サポートされていないMIMEタイプによりAIの応答がブロックされました: {e}")
            return None
        except genai_types.BlockedReasonException as e: # Gemini固有の例外
            logging.error(f"AIの応答がブロックされました: {e}")
            return None
        except genai.core.exceptions.GoogleGenerativeAIException as e: # その他のGemini APIエラー
            logging.error(f"Gemini APIエラーが発生しました: {e} (試行 {attempt + 1}/{MAX_RETRIES})。再試行します...")
        except Exception as e:
            logging.error(f"AI API呼び出し中に予期せぬエラーが発生しました: {e} (試行 {attempt + 1}/{MAX_RETRIES})。再試行します...")
        
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY_SECONDS)
    
    logging.error(f"AI API呼び出しが{MAX_RETRIES}回試行されましたが、すべて失敗しました。")
    return None
```

**補足:**

*   `genai.core.exceptions`モジュールは、Gemini APIクライアントライブラリの内部構造に依存するため、将来的にパスが変わる可能性がある点に注意が必要です。
*   `json.JSONDecodeError`は、Ollamaからの応答がJSON形式でない場合に発生する可能性があります。
*   `BlockedPromptException`などのGemini固有の例外は、Gemini APIの利用規約に違反するようなプロンプトを送信した場合に発生します。これらのエラーは再試行しても解決しないため、即座に処理を終了するようにします。