public with sharing class PaymentService {
    @AuraEnabled
    public static String createPaymentIntent(Decimal amount, String currencyIsoCode) {
        HttpRequest req = new HttpRequest();
        req.setMethod('POST');
        req.setEndpoint('callout:Stripe_Endpoint/v1/payment_intents');
        req.setHeader('Content-Type', 'application/x-www-form-urlencoded');

        String body =
            'amount=' + EncodingUtil.urlEncode(String.valueOf((Integer)(amount * 100)), 'UTF-8') +
            '&currency=' + EncodingUtil.urlEncode(currencyIsoCode, 'UTF-8');
        req.setBody(body);

        HttpResponse res = new Http().send(req);
        if (res.getStatusCode() >= 200 && res.getStatusCode() < 300) {
            return res.getBody();
        }
        throw new AuraHandledException('Unable to create payment intent: ' + res.getBody());
    }
}
