@IsTest
private class PaymentServiceTest {
    private class SuccessMock implements HttpCalloutMock {
        public HttpResponse respond(HttpRequest req) {
            HttpResponse res = new HttpResponse();
            res.setStatusCode(200);
            res.setBody('{"id":"pi_123"}');
            return res;
        }
    }

    @IsTest
    static void returnsStripeBodyOnSuccess() {
        Test.setMock(HttpCalloutMock.class, new SuccessMock());

        Test.startTest();
        String responseBody = PaymentService.createPaymentIntent(12.34, 'usd');
        Test.stopTest();

        System.assert(responseBody.contains('pi_123'));
    }
}
