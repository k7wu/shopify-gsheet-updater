# shopify-gsheet-updater
This repo contains scripts and files necessary to deploy, with some customization, an automated daily-aggregated order data integration between Shopify & a Google sheet of your choice. Fork the repo, make any necessary changes to the script, and push it to your own Heroku account.

This simple background process uses Shopify's REST API, Google Sheet's API libraries, Pandas, and a simple scheduler ([APScheduler](https://apscheduler.readthedocs.io/en/stable/)) all deployed on a free Heroku dyno.

## Step 1: Enable Private Apps on your Shopify Store
Follow the instructions [here](https://shopify.dev/tutorials/make-your-first-shopify-api-request#generate-api-credentials-from-the-shopify-admin) to enable private apps for your Shopify Store and acquire your API Key and Token. Ensure you enable "read" access to your orders.

## Step 2: Obtain Google Sheet OAuth Credentials
Follow the instructions [here](https://developers.google.com/sheets/api/quickstart/python) to obtain your credentials.json & .pickle authorization files. Alternatively, review the documentation on how to implement OAuth from Heroku and extend the code accordingly. Include the access credential files in the group of files you will deploy onto Heroku.

## Step 3: Fork the repo, update the code
Fork this repo and modify the script so that it contains your Shopify API storename for the REST API endpoint, your Secret Key & Token (for more security, extend the code so that your key-token pair are saved as [environment/config variables in your Heroku dyno](https://devcenter.heroku.com/articles/config-vars)), and your google sheet spreadsheet ID & name. If you want to adjust what the script reports, adjust the parameters & pandas section in the script accordingly. Shopify's Order API reference is available [here](https://shopify.dev/docs/admin-api/rest/reference/orders/order?api[version]=2020-04).

## Step 4: Push the project to a Heroku Dyno, Scale your Clock, and you're good to go.
Follow the documentation [here](https://devcenter.heroku.com/articles/getting-started-with-python) to deploy the code onto your Heroku account. To get the scheduler running, scale the heroku dyno's clock following the documentation [here](https://devcenter.heroku.com/articles/clock-processes-python). Once everything is set up, you should be good to go! Your daily aggregated order data will update at midnight every night.

### Caveat
Currently, the data aggregation, specifically revenue related figures, do not always match with Shopify's Reports in the Admin console. This is a known issue which may be dealt with in time.
