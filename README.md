SS_temp_read2について
PCの画面のSSを指定時間ごとに取ってOCR処理をし、CSVログへ掃き出すプログラム。
取得ボタンを押すことで半透明のキャンバスが出現しドラッグすることでSSの範囲をフィードバックする。その後時間間隔を設定する。
tesseractをインストールしpathに追加する必要がある。(コントロールパネル->システム->環境変数を編集->path->編集->インストール先を追加)
多分デフォルトのままインストールしたならC:\Program Files\Tesseract-OCR\でpathの設定はできるはず。
最後に\を入れないと認識しないから注意

SS_tempについて
PCの画面のSSを指定時間ごとに取って保存するプログラム。
取得ボタンを押すことで半透明のキャンバスが出現しドラッグすることでSSの範囲をフィードバックする。その後時間間隔を設定する。
新規保存か上書き保存かを選べます。
