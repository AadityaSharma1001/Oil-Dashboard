import httpx
resp = httpx.get('https://publicreporting.cftc.gov/resource/6dca-aqww.json', params={
    '$where': "commodity_name='CRUDE OIL, LIGHT SWEET'",
    '$order': "report_date_as_yyyy_mm_dd DESC",
    '$limit': 1
})
print("STATUS:", resp.status_code)
if resp.status_code == 200:
    data = resp.json()
    print("DATA:", data)
else:
    print("TEXT:", resp.text)
