EC_Event__c eventRecord = new EC_Event__c(
    Name = 'Seeded Demo Event',
    Capacity__c = 150,
    Start_Date__c = Date.today().addDays(14)
);
insert eventRecord;

EC_Grant__c grantRecord = new EC_Grant__c(
    Name = 'Seeded Community Grant',
    Deadline__c = Date.today().addDays(45),
    Funding_Amount__c = 25000
);
insert grantRecord;
