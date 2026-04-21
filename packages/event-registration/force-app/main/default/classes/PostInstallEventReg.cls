global class PostInstallEventReg implements InstallHandler {
    global void onInstall(InstallContext context) {
        try {
            insert new EC_Event__c(
                Name = 'Sample Event - Delete Me',
                Capacity__c = 100,
                Start_Date__c = Date.today().addDays(30)
            );
        } catch (DmlException de) {
            // Keep install resilient if sample seed fails.
        }
    }
}
