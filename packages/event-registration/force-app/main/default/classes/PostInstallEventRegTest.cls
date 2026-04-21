@IsTest
private class PostInstallEventRegTest {
    @IsTest
    static void seedsSampleEvent() {
        Test.startTest();
        new PostInstallEventReg().onInstall(null);
        Test.stopTest();
        System.assertEquals(1, [SELECT COUNT() FROM EC_Event__c WHERE Name = 'Sample Event - Delete Me']);
    }
}
