# gsuite_samlapi_formauth
get temporary security token for federation users using saml2.0 with g suite authentication.

## Description
G Suiteの認証を利用して、AWSの一時認証情報を取得するスクリプト。
取得した情報は、~/.aws/credentialsのsamlセクションへ書き出されます。

*** DEMO: ***


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


