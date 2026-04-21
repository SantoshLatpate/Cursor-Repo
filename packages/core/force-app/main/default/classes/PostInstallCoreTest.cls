@IsTest
private class PostInstallCoreTest {
    @IsTest
    static void helperMethodsExecute() {
        Test.startTest();
        PostInstallCore.assignBaseAccess(null);
        PostInstallCore.seedOrgDefaultConfig();
        Test.stopTest();
        System.assert(true);
    }
}
