/**
 * Builds the LCSPTF 14th Annual Suicide Prevention & Awareness Walk/Run
 * participant survey (10 questions) as a Google Form, plus a linked
 * Google Sheet for responses.
 *
 * People who couldn't attend skip the event questions and only answer
 * the first question and the last three.
 *
 * Run it from any Google account to practice: the form is named "PRACTICE"
 * and stays in that account's My Drive. Run it from the Task Force account
 * (prevention.lcsptf@gmail.com) to make the real survey, which is filed in
 * the Walk Shared Folder.
 *
 * How to use:
 *   1. Go to https://script.google.com and click "New project".
 *   2. Delete the sample code, paste this whole file in, and click Save.
 *   3. Click "Run" (with buildWalkSurvey selected) and approve the permissions.
 *   4. Open "Execution log" to find the links to your new form and sheet.
 */

var TASK_FORCE_ACCOUNT = 'prevention.lcsptf@gmail.com';

// The Task Force's "Walk Shared Folder" in Google Drive.
var WALK_SHARED_FOLDER_ID = '1T_Xxe4e6NEagLJ6gYW8v07hXoecI-8aX';

function buildWalkSurvey() {
  var account = Session.getEffectiveUser().getEmail();
  var isRealSurvey = account.toLowerCase() === TASK_FORCE_ACCOUNT;
  var prefix = isRealSurvey ? '' : 'PRACTICE – ';

  var form = FormApp.create(prefix + "LCSPTF's 14th Annual Suicide Prevention & Awareness Walk/Run – Participant Survey");

  form.setDescription(
    'Thank you for being part of this year\'s Walk/Run! Your feedback helps us make next year\'s event even better. ' +
    'This survey takes about 3 minutes, and every question is optional. Your responses are anonymous.\n\n' +
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

  // ---- 1. How did you take part? ----
  // Choices are set at the end, once the sections they jump to exist.
  var takePart = form.addMultipleChoiceItem()
    .setTitle('How did you take part this year?');

  // ---- Your Experience (everyone who took part) ----
  var experience = form.addPageBreakItem()
    .setTitle('Your Experience');

  // 2
  form.addMultipleChoiceItem()
    .setTitle('Overall, how was your experience?')
    .setChoiceValues([
      'Excellent',
      'Very good',
      'Good',
      'Fair',
      'Poor'
    ]);

  // 3
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

  // 4
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

  // 5
  form.addMultipleChoiceItem()
    .setTitle('Did you use Early Check-in and T-Shirt Pick-up on September 19?')
    .setChoiceValues([
      'Yes, and it went smoothly',
      'Yes, but it could be improved',
      'No, I prefer checking in on the day of the event',
      'No, the date or time didn\'t work for me',
      'I didn\'t know about it'
    ]);

  // 6
  form.addMultipleChoiceItem()
    .setTitle('The Kick-Off ran for half an hour (10:00–10:30). Was that:')
    .setChoiceValues([
      'Too short',
      'About right',
      'Too long'
    ]);

  // 7
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

  // 8
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

  // 9
  form.addMultipleChoiceItem()
    .setTitle('Will you join us next year?')
    .setChoiceValues([
      'Definitely',
      'Probably',
      'Not sure'
    ]);

  // 10
  form.addParagraphTextItem()
    .setTitle('Is there anything else you\'d like to share?');

  // Send people who couldn't attend straight to the last questions.
  takePart.setChoices([
    takePart.createChoice('At the College of Lake County', experience),
    takePart.createChoice('I walked/ran on my own, somewhere else', experience),
    takePart.createChoice('I watched on Facebook Live', experience),
    takePart.createChoice('I couldn\'t make it this year', lastQuestions)
  ]);

  // Linked spreadsheet for responses.
  var sheet = SpreadsheetApp.create(prefix + 'LCSPTF Walk/Run Survey – Responses');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, sheet.getId());

  // Newer Google Forms start unpublished; publish if this account supports it.
  try {
    form.setPublished(true);
  } catch (e) {
    // Older behavior: forms are already accepting responses.
  }

  // File the real survey in the Walk Shared Folder; practice copies stay in My Drive.
  var where = 'My Drive';
  if (isRealSurvey) {
    try {
      var folder = DriveApp.getFolderById(WALK_SHARED_FOLDER_ID);
      DriveApp.getFileById(form.getId()).moveTo(folder);
      DriveApp.getFileById(sheet.getId()).moveTo(folder);
      where = 'the Walk Shared Folder';
    } catch (e) {
      where = 'My Drive (the Walk Shared Folder could not be reached)';
    }
  }

  Logger.log(isRealSurvey ? 'This is the REAL survey.' : 'This is a PRACTICE survey (run as ' + account + ').');
  Logger.log('Share this link with participants: ' + form.getPublishedUrl());
  Logger.log('Edit the form here: ' + form.getEditUrl());
  Logger.log('Responses spreadsheet: ' + sheet.getUrl());
  Logger.log('Both files were saved in ' + where + '.');
}
