# gsuite_samlapi_formauth
get temporary security token for federation users using saml2.0 with g suite authentication.

## Description
G Suiteの認証を利用して、AWSの一時認証情報を取得するスクリプト。
取得した情報は、~/.aws/credentialsのsamlセクションへ書き出されます。

*** DEMO: ***
<script type="text/javascript" src="https://asciinema.org/a/cu382jvwzb7cl7p8fic0ignr1.js" id="asciicast-cu382jvwzb7cl7p8fic0ignr1" async></script>


## Requirement
- PhantomJS
  - JavaScriptの実行上するブラウザとして使用する
  ```
  brew install phantomjs
  ```
- selenium
- request
- lxml
- beautifulsoup
  ```
  pip install selenium
  pip install requests
  pip install lxml
  pip install beautifulsoup4
  ```


