export type SourceSystem = 'PARLIAMENT' | 'LEGISLATION' | 'GAZETTE' | 'BEEHIVE';

export interface StageHistory {
  stage: string;
  date: string;
}

export interface ActionMetadata {
  bill_number?: string;
  parliament_number?: number;
  stage_history?: StageHistory[];
  act_number?: string;
  commencement_date?: string;
  notice_number?: string;
  notice_type?: string;
  document_type?: string;
  portfolio?: string;
}

export interface GovernmentAction {
  id: string;
  title: string;
  date: string;
  source_system: SourceSystem;
  url: string;
  primary_entity: string;
  summary: string;
  labels: string[];
  metadata: ActionMetadata;
}

export const labels = [
  'Housing',
  'Health',
  'Education',
  'Infrastructure',
  'Environment',
  'Economy',
  'Justice',
  'Immigration',
  'Defence',
  'Transport',
  'Social Welfare',
  'Tax',
  'Local Government',
  'Treaty of Waitangi',
  'Agriculture',
];

export const fixtureActions: GovernmentAction[] = [
  {
    id: 'parl-2024-001',
    title: 'Fast-track Approvals Bill',
    date: '2024-12-05',
    source_system: 'PARLIAMENT',
    url: 'https://bills.parliament.nz/v/6/00DBHOH_BILL131541_1',
    primary_entity: 'Hon Chris Bishop',
    summary: 'A bill to provide a fast-track consenting process for major infrastructure and development projects, streamlining approvals under the Resource Management Act.',
    labels: ['Infrastructure', 'Housing', 'Environment'],
    metadata: {
      bill_number: '131541',
      parliament_number: 54,
      stage_history: [
        { stage: 'First Reading', date: '2024-03-21' },
        { stage: 'Select Committee', date: '2024-04-15' },
        { stage: 'Second Reading', date: '2024-09-10' },
        { stage: 'Committee of the whole House', date: '2024-11-28' },
        { stage: 'Third Reading', date: '2024-12-05' },
      ],
    },
  },
  {
    id: 'parl-2024-002',
    title: 'Gangs Legislation Amendment Bill',
    date: '2024-11-28',
    source_system: 'PARLIAMENT',
    url: 'https://bills.parliament.nz/v/6/00DBHOH_BILL136801_1',
    primary_entity: 'Hon Mark Mitchell',
    summary: 'Introduces new powers to disperse gang members and prohibit gang insignia in public places.',
    labels: ['Justice'],
    metadata: {
      bill_number: '136801',
      parliament_number: 54,
      stage_history: [
        { stage: 'First Reading', date: '2024-05-02' },
        { stage: 'Select Committee', date: '2024-06-20' },
        { stage: 'Second Reading', date: '2024-11-28' },
      ],
    },
  },
  {
    id: 'leg-2024-001',
    title: 'Taxation (Annual Rates for 2024–25, Emergency Response, and Remedial Measures) Act 2024',
    date: '2024-11-14',
    source_system: 'LEGISLATION',
    url: 'https://www.legislation.govt.nz/act/public/2024/0052/latest/LMS961557.html',
    primary_entity: 'Hon Nicola Willis',
    summary: 'Sets the annual rates of income tax for the 2024–25 tax year and introduces various tax policy changes including FamilyBoost childcare payments.',
    labels: ['Tax', 'Economy', 'Social Welfare'],
    metadata: {
      act_number: '2024 No 52',
      commencement_date: '2024-11-14',
    },
  },
  {
    id: 'leg-2024-002',
    title: 'Resource Management (Extended Duration of Coastal Permits for Marine Farms) Amendment Act 2024',
    date: '2024-10-31',
    source_system: 'LEGISLATION',
    url: 'https://www.legislation.govt.nz/act/public/2024/0048/latest/LMS924688.html',
    primary_entity: 'Hon Shane Jones',
    summary: 'Extends the maximum duration of coastal permits for existing marine farms from 20 to 35 years.',
    labels: ['Environment', 'Agriculture'],
    metadata: {
      act_number: '2024 No 48',
      commencement_date: '2024-10-31',
    },
  },
  {
    id: 'gaz-2024-001',
    title: 'Appointment of District Court Judge',
    date: '2024-12-02',
    source_system: 'GAZETTE',
    url: 'https://gazette.govt.nz/notice/id/2024-vr3456',
    primary_entity: 'Governor-General',
    summary: 'Appointment of Sarah Thompson as a Judge of the District Court of New Zealand.',
    labels: ['Justice'],
    metadata: {
      notice_number: '2024-vr3456',
      notice_type: 'Vice Regal',
      portfolio: 'Justice',
    },
  },
  {
    id: 'gaz-2024-002',
    title: 'Land Transport Rule: Vehicle Dimensions and Mass Amendment 2024',
    date: '2024-11-25',
    source_system: 'GAZETTE',
    url: 'https://gazette.govt.nz/notice/id/2024-go4521',
    primary_entity: 'Hon Simeon Brown',
    summary: 'Amends vehicle dimension and mass requirements for heavy vehicles on New Zealand roads.',
    labels: ['Transport', 'Infrastructure'],
    metadata: {
      notice_number: '2024-go4521',
      notice_type: 'General',
      portfolio: 'Transport',
    },
  },
  {
    id: 'bee-2024-001',
    title: 'Government announces $1.5 billion infrastructure boost',
    date: '2024-12-04',
    source_system: 'BEEHIVE',
    url: 'https://www.beehive.govt.nz/release/government-announces-infrastructure-boost',
    primary_entity: 'Rt Hon Christopher Luxon',
    summary: 'The Government has announced a $1.5 billion investment in roads, schools and hospitals over the next three years.',
    labels: ['Infrastructure', 'Transport', 'Health', 'Education'],
    metadata: {
      document_type: 'Press Release',
      portfolio: 'Prime Minister',
    },
  },
  {
    id: 'bee-2024-002',
    title: 'New measures to address housing crisis',
    date: '2024-11-30',
    source_system: 'BEEHIVE',
    url: 'https://www.beehive.govt.nz/release/new-measures-housing-crisis',
    primary_entity: 'Hon Chris Bishop',
    summary: 'Housing Minister announces changes to density rules and infrastructure funding to accelerate housing development.',
    labels: ['Housing', 'Infrastructure', 'Local Government'],
    metadata: {
      document_type: 'Press Release',
      portfolio: 'Housing',
    },
  },
  {
    id: 'bee-2024-003',
    title: 'Speech to Business NZ Annual Conference',
    date: '2024-11-22',
    source_system: 'BEEHIVE',
    url: 'https://www.beehive.govt.nz/speech/business-nz-annual-conference',
    primary_entity: 'Rt Hon Christopher Luxon',
    summary: 'Prime Minister outlines the Government\'s economic priorities and regulatory reform agenda.',
    labels: ['Economy'],
    metadata: {
      document_type: 'Speech',
      portfolio: 'Prime Minister',
    },
  },
  {
    id: 'parl-2024-003',
    title: 'Treaty Principles Bill',
    date: '2024-11-14',
    source_system: 'PARLIAMENT',
    url: 'https://bills.parliament.nz/v/6/00DBHOH_BILL136899_1',
    primary_entity: 'Hon David Seymour',
    summary: 'A bill to define the principles of the Treaty of Waitangi for the purposes of New Zealand law.',
    labels: ['Treaty of Waitangi', 'Justice'],
    metadata: {
      bill_number: '136899',
      parliament_number: 54,
      stage_history: [
        { stage: 'First Reading', date: '2024-11-14' },
      ],
    },
  },
  {
    id: 'leg-2024-003',
    title: 'Education and Training Amendment Act 2024',
    date: '2024-09-30',
    source_system: 'LEGISLATION',
    url: 'https://www.legislation.govt.nz/act/public/2024/0041/latest/LMS123456.html',
    primary_entity: 'Hon Erica Stanford',
    summary: 'Amends the Education and Training Act 2020 to strengthen requirements for structured literacy in schools.',
    labels: ['Education'],
    metadata: {
      act_number: '2024 No 41',
      commencement_date: '2024-10-01',
    },
  },
  {
    id: 'gaz-2024-003',
    title: 'Health New Zealand Board Appointments',
    date: '2024-11-15',
    source_system: 'GAZETTE',
    url: 'https://gazette.govt.nz/notice/id/2024-go4123',
    primary_entity: 'Hon Dr Shane Reti',
    summary: 'Appointments to the Board of Health New Zealand Te Whatu Ora.',
    labels: ['Health'],
    metadata: {
      notice_number: '2024-go4123',
      notice_type: 'General',
      portfolio: 'Health',
    },
  },
];
