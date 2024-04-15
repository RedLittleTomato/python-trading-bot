import requests
import uuid
import json

client_request_id = str(uuid.uuid4())

url = 'https://www.etoro.com/api/logininfo/v1.1/logindata'
payload = {
  'client_request_id': client_request_id,
  'conditionIncludeDisplayableInstruments': 'false',
  'conditionIncludeMarkets': 'false',
  'conditionIncludeMetadata': 'false',
  'conditionIncludeMirrorValidation': 'false'
}
headers = {
  'authority': 'www.etoro.com',

  'accept': 'application/json, text/plain, */*',
  # 'accept-encoding': 'gzip, deflate, br',
  # 'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7',
  'accounttype': 'Demo',
  'applicationidentifier': 'ReToro',
  'applicationversion': '309.0.2',
  'authorization': 'qOAHhx9iSKhOjJG6ce9fh9QzWFGKjTdIueiRDG03yrjt6rQpYwsthie%7CglPLS9RoJrmo-65nVtVltVszc8GrP85%7Cfynjl5kgd3JrSoUwWq9Z44F33xeFeHCDkKWmPEtB%7CuIZsWYhJLn5SJRvnkshyaz5VyiEegU0laDkcXiHkTT5kbPQnMwqqyCJYIvqHDd8KbGRkTtqW9aZ7di-i9ZNFm8p9r48TlQ%7CDeOkZHXpjqwiYhbRD5vPEKEn5-sxpaGJ6hqARN6dCUzn0W6auJg2bnRJA396-QaRkYVpWnjngJOFnzLLq3QO9fRYlOEpB9df0DN84yXlG3gOns1vC5RqvA__',
  # 'content-length': 519,
  'content-type': 'application/json;charset=UTF-8',
  'cookie': 'G_ENABLED_IDPS=google; liveagent_oref=; liveagent_sid=6e604876-9cb0-4f94-98f7-fd4e4e7dbe04; liveagent_vc=2; liveagent_ptid=6e604876-9cb0-4f94-98f7-fd4e4e7dbe04; visid_incap_1964444=DIFq4jh6QweYm8Qply02msbI1V4AAAAAQUIPAAAAAAAtpDrwJOrbCOP78+/7vJQv; incap_ses_1129_1964444=LzFWcaeRu3wkkWD9lAOrD8fI1V4AAAAAzU/t1qhyHVJfC4G212bzqA==; ajs_group_id=null; ajs_anonymous_id=%22ff23dc49-5247-45fd-98ee-9170f44f0307%22; TS01b45bb7=01d53e5818dd1703904809b3f81cb2a0fe3ea6426276921363a9b3ff2e4b439ecc55b47b074a9b1067538db3934252f3684a77a162; hp_abc=b; etoroHPRedirect=1; __cfduid=d2b6721a2415a3cc904d999604ac6334e1612164610; eToroLocale=en-gb; AffiliateWizAffiliateID=AffiliateID=81433&ClickBannerID=0&SubAffiliateID=&Custom=&ClickDateTime=2021-02-25T15:42:03.6079261Z&UserUniqueIdentifier=; RequestURL=URL=http://partners.etoro.com/aw.aspx?a=81433&task=click; __cfruid=95d1ae3e17f00b1cf4a19f0c659db67b0c969fe0-1614609126; __cf_bm=2a6ba83030b81766c68f58f3788061199b271f5c-1614619929-1800-Ae/t7HUV3gaOgcngnUvzXEQkhsmHrtvPFysAj1Cx7pEDZrh0wrOp3LKoAoYRt4l12FMhe9vMcvmE0s3/ZsWhh4xOga6kYlv6k9y2D8DMDscR; TMIS2=9a74f2a902374869ae4dcb925ac5c5511925a1e02fb7a36481f461311e3d1bd929198bd5f3020b37e3e067d927f5e9dad6d6306df04bac744a3c3a69ace49dd0b4a25bf549ebc653902b3483538bcbe24fd7297cdf0c512e738927b62732627c527ba4d3a66ad88c3c46cd0d24df35f8fe9b6f60a6c915850f702077521fd69d; __cflb=02rXhV1zWDyEwS3zFc3FH4ByX4Z536jjuw3Rcxb1MREUjqY4z47LgrJHJP1HkAYvtZoLPRHLwWj7f4br178c2xGdCFQowwWd3Y6HTW9YVd5qcdY2m2wDMWFaM7R7t6tEy2hnta49eHVEvDhxwAHucAvfPy2MiHrPpta2GmcTfNKYhvq2; TS01047baf=01f1b32d7ec45bf139dfce5fde205f4603c7b9624c54be7eea2fbcd250c08338757cc0edff74e21784f1d2a58cdc0ae9ad692f82ec',
  # 'dnt': 1,
  'origin': 'https://www.etoro.com',
  'referer': 'https://www.etoro.com/watchlists',
  'sec-fetch-site': 'same-origin',
  'sec-fetch-mode': 'cors',
  'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
  'x-sts-appdomain': 'https://www.etoro.com',
  'x-sts-gatewayappid': '90631448-9A01-4860-9FA5-B4EBCDE5EA1D',
}

r = requests.get(url, json=payload, headers=headers)
print(r.text)