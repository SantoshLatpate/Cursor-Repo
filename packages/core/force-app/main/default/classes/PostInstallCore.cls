global class PostInstallCore implements InstallHandler {
    global void onInstall(InstallContext context) {
        assignBaseAccess(context);
        seedOrgDefaultConfig();
    }

    @TestVisible
    private static void assignBaseAccess(InstallContext context) {
        PermissionSet ps;
        try {
            ps = [SELECT Id FROM PermissionSet WHERE Name = 'EC_Base_Access' LIMIT 1];
        } catch (QueryException qe) {
            return;
        }

        Id installerId = (context != null && context.installerId() != null)
            ? context.installerId()
            : UserInfo.getUserId();

        if ([SELECT COUNT() FROM PermissionSetAssignment WHERE AssigneeId = :installerId AND PermissionSetId = :ps.Id] == 0) {
            try {
                insert new PermissionSetAssignment(AssigneeId = installerId, PermissionSetId = ps.Id);
            } catch (DmlException de) {
                // Ignore assignment failures so package installation can proceed.
            }
        }
    }

    @TestVisible
    private static void seedOrgDefaultConfig() {
        Map<String, Schema.SObjectType> globalTypes = Schema.getGlobalDescribe();
        if (!globalTypes.containsKey('EC_Config__c')) {
            return;
        }

        SObject config = globalTypes.get('EC_Config__c').newSObject();
        config.put('SetupOwnerId', UserInfo.getOrganizationId());
        Database.upsert(config, false);
    }
}
