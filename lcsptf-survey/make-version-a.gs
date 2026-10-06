/**
 * Builds "Version A" of the Walk/Run Participant Survey for the group to
 * compare with the current survey, which is left untouched.
 *
 * Version A has the same 10 questions plus an "At the Event" section
 * (resource tables, food trucks, Kick-Off presentations) that only CLC
 * attendees see. It gets its own responses spreadsheet, and both files are
 * saved in the Walk Shared Folder.
 *
 * How to use:
 *   1. Open your Apps Script project and replace the code with this file.
 *   2. Click Save, choose makeVersionA next to Debug, and click Run.
 *   3. Open "Execution log" to find the links to Version A.
 */

var VERSION_A_TITLE = 'Walk/Run Participant Survey 2026 – A';

// The Task Force's "Walk Shared Folder" in Google Drive.
var WALK_SHARED_FOLDER_ID = '1T_Xxe4e6NEagLJ6gYW8v07hXoecI-8aX';

function makeVersionA() {
  var form = FormApp.create(VERSION_A_TITLE);

  form.setDescription(
    'Thank you for being part of this year\'s Walk/Run! Your feedback helps us make next year\'s event even better. ' +
    'This survey takes about 3–4 minutes, and every question is optional. Your responses are anonymous.\n\n' +
    'If this event brought up difficult feelings, you\'re not alone. Call or text 988 anytime to reach the ' +
    'Suicide & Crisis Lifeline.'
  );

  form.setConfirmationMessage(
    'Thank you so much for walking with us, and for taking the time to share your thoughts! Every step taken ' +
    'together is a reminder that no one has to walk alone. We look forward to seeing you next year!\n\n' +
    'If you or someone you love is struggling, help is always available. Call or text 988 to reach the ' +
    'Suicide & Crisis Lifeline, 24 hours a day.'
  );

  // Keep responses anonymous: no email collection, no sign-in required.
  try {
    form.setEmailCollectionType(FormApp.EmailCollectionType.DO_NOT_COLLECT);
  } catch (e) {
    form.setCollectEmail(false);
  }
  try {
    form.setRequireLogin(false); // Only available on Google Workspace accounts.
  } catch (e) {}
  form.setLimitOneResponsePerUser(false);
  form.setAllowResponseEdits(false);
  form.setShowLinkToRespondAgain(false);
  form.setProgressBar(true);

  // ---- How did you take part? ----
  // Choices are set at the end, once the sections they jump to exist.
  var takePart = form.addMultipleChoiceItem()
    .setTitle('How did you take part this year?');

  // ---- At the Event (CLC attendees only) ----
  var atEvent = form.addPageBreakItem()
    .setTitle('At the Event');

  form.addMultipleChoiceItem()
    .setTitle('Regarding the Resource Tables:')
    .setChoiceValues([
      'I visited them and found them helpful',
      'I visited them, but they weren\'t very helpful',
      'I didn\'t visit them – I wasn\'t interested',
      'I didn\'t visit them – I didn\'t have time',
      'I didn\'t know there were resource tables'
    ]);

  form.addParagraphTextItem()
    .setTitle('Which resources were most helpful, or what would you like to see added?');

  form.addMultipleChoiceItem()
    .setTitle('Regarding the Food Trucks:')
    .setChoiceValues([
      'I appreciated having the food trucks',
      'I didn\'t use them, but it\'s nice to have them',
      'I\'d prefer not to have food trucks'
    ]);

  form.addCheckboxItem()
    .setTitle('Regarding the Kick-Off and Presentations:')
    .setHelpText('Check any that apply.')
    .setChoiceValues([
      'I appreciated the speakers and hearing their stories',
      'I could see and hear the presentations well',
      'I had trouble seeing or hearing the presentations',
      'I chose not to listen to the presentations',
      'I arrived after the presentations'
    ]);

  // ---- Your Experience (everyone who took part) ----
  var experience = form.addPageBreakItem()
    .setTitle('Your Experience');

  form.addMultipleChoiceItem()
    .setTitle('Overall, how was your experience?')
    .setChoiceValues([
      'Excellent',
      'Very good',
      'Good',
      'Fair',
      'Poor'
    ]);

  form.addCheckboxItem()
    .setTitle('What meant the most to you?')
    .setHelpText('Check any that apply.')
    .setChoiceValues([
      'Walking alongside others',
      'Hearing the speakers\' stories',
      'The resource tables',
      'The food trucks',
      'The overall sense of community and hope',
      'Something else'
    ]);

  form.addCheckboxItem()
    .setTitle('What could we do better next year?')
    .setHelpText('Check any that apply.')
    .setChoiceValues([
      'More information before the event',
      'Fewer emails',
      'Better sound or view during the Kick-Off',
      'A different location',
      'Everything was great!'
    ]);

  form.addMultipleChoiceItem()
    .setTitle('Did you use Early Check-in and T-Shirt Pick-up on September 19?')
    .setChoiceValues([
      'Yes, and it went smoothly',
      'Yes, but it could be improved',
      'No, I prefer checking in on the day of the event',
      'No, the date or time didn\'t work for me',
      'I didn\'t know about it'
    ]);

  form.addMultipleChoiceItem()
    .setTitle('The Kick-Off ran for half an hour (10:00–10:30). Was that:')
    .setChoiceValues([
      'Too short',
      'About right',
      'Too long'
    ]);

  form.addMultipleChoiceItem()
    .setTitle('Where should next year\'s walk be held?')
    .setHelpText('Have a location idea? Please share it in the last question.')
    .setChoiceValues([
      'Keep it at CLC',
      'Try somewhere new',
      'No preference'
    ]);

  // ---- A Few Last Questions (everyone) ----
  var lastQuestions = form.addPageBreakItem()
    .setTitle('A Few Last Questions');

  form.addCheckboxItem()
    .setTitle('How did you hear about the walk?')
    .setHelpText('Check any that apply.')
    .setChoiceValues([
      'I\'ve come before',
      'Family or friend',
      'LCSPTF email or website',
      'Social media',
      'Church or faith community',
      'Flyer, radio, or other'
    ]);

  form.addMultipleChoiceItem()
    .setTitle('Will you join us next year?')
    .setChoiceValues([
      'Definitely',
      'Probably',
      'Not sure'
    ]);

  form.addParagraphTextItem()
    .setTitle('Is there anything else you\'d like to share?');

  // CLC attendees see the At the Event section; others skip ahead.
  takePart.setChoices([
    takePart.createChoice('At the College of Lake County', atEvent),
    takePart.createChoice('I walked/ran on my own, somewhere else', experience),
    takePart.createChoice('I watched on Facebook Live', experience),
    takePart.createChoice('I couldn\'t make it this year', lastQuestions)
  ]);

  // Version A gets its own responses spreadsheet.
  var sheet = SpreadsheetApp.create(VERSION_A_TITLE + ' – Responses');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, sheet.getId());

  try {
    form.setPublished(true);
  } catch (e) {
    // Older behavior: forms are already accepting responses.
  }

  var where = 'the Walk Shared Folder';
  try {
    var folder = DriveApp.getFolderById(WALK_SHARED_FOLDER_ID);
    DriveApp.getFileById(form.getId()).moveTo(folder);
    DriveApp.getFileById(sheet.getId()).moveTo(folder);
  } catch (e) {
    where = 'My Drive (the Walk Shared Folder could not be reached)';
  }

  Logger.log('Version A survey link: ' + form.getPublishedUrl());
  Logger.log('Edit Version A here: ' + form.getEditUrl());
  Logger.log('Version A responses: ' + sheet.getUrl());
  Logger.log('Both files were saved in ' + where + '. The current survey was not changed.');
}
