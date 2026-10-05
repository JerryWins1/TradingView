/**
 * Builds the LCSPTF 14th Annual Suicide Prevention & Awareness Walk/Run
 * participant survey as a Google Form, plus a linked Google Sheet for responses.
 *
 * The form uses sections so each person only sees questions that fit how
 * they took part:
 *   - Attended at CLC:            At the Event -> Kick-Off -> Overall -> Last Questions
 *   - Watched on Facebook Live:   Kick-Off -> Overall -> Last Questions
 *   - Walked somewhere else:      Overall -> Last Questions
 *   - Didn't participate:         Last Questions
 *
 * How to use:
 *   1. Go to https://script.google.com and click "New project".
 *   2. Delete the sample code, paste this whole file in, and click Save.
 *   3. Click "Run" (with buildWalkSurvey selected) and approve the permissions.
 *   4. Open "Execution log" to find the links to your new form and sheet.
 */

// The Task Force's "Walk Shared Folder" in Google Drive.
var WALK_SHARED_FOLDER_ID = '1T_Xxe4e6NEagLJ6gYW8v07hXoecI-8aX';

function buildWalkSurvey() {
  var form = FormApp.create("LCSPTF's 14th Annual Suicide Prevention & Awareness Walk/Run – Participant Survey");

  form.setDescription(
    'Thank you for being part of this year\'s Walk/Run! Your feedback helps us make next year\'s event even better. ' +
    'This survey takes about 3–5 minutes, and every question is optional. Your responses are anonymous.\n\n' +
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

  // ---- Section 1: How did you participate? ----
  // Choices are set at the end, once the sections they jump to exist.
  var participation = form.addMultipleChoiceItem()
    .setTitle('How did you participate in this year\'s event?');

  // ---- Section 2: At the Event (CLC attendees only) ----
  var atEvent = form.addPageBreakItem()
    .setTitle('At the Event');

  form.addMultipleChoiceItem()
    .setTitle('Regarding the Resource Tables:')
    .setChoiceValues([
      'I visited them and found them helpful',
      'I visited them and did not find them helpful',
      'I didn\'t visit them – I wasn\'t interested',
      'I didn\'t visit them – I didn\'t have time',
      'I didn\'t know there were resource tables'
    ]);
  form.addParagraphTextItem()
    .setTitle('Which tables were most helpful, or what would you like to see added?');

  form.addMultipleChoiceItem()
    .setTitle('Regarding the Food Trucks:')
    .setChoiceValues([
      'I appreciated having the food trucks',
      'I didn\'t use them, but it\'s nice to have them',
      'I\'d prefer not to have food trucks'
    ]);
  form.addParagraphTextItem()
    .setTitle('Any comments about the food trucks?');

  form.addMultipleChoiceItem()
    .setTitle('Regarding the Venue:')
    .setChoiceValues([
      'I like having the event at CLC',
      'I\'d prefer a different venue next year',
      'No preference'
    ]);
  form.addParagraphTextItem()
    .setTitle('Any comments about the venue or course, including suggestions for other locations or areas of the county?');

  // ---- Section 3: Kick-Off (CLC attendees and Facebook Live viewers) ----
  var kickOff = form.addPageBreakItem()
    .setTitle('The Kick-Off and Presentations');

  form.addCheckboxItem()
    .setTitle('Regarding the Kick-Off and Presentations:')
    .setHelpText('Check all that apply.')
    .setChoiceValues([
      'I appreciated the speakers and hearing their stories',
      'I was able to see and hear the presentations well',
      'I had difficulty seeing or hearing the presentations',
      'I chose not to listen to the presentations',
      'I arrived after the presentations'
    ]);

  form.addMultipleChoiceItem()
    .setTitle('The Kick-Off ran for half an hour (10:00–10:30). Was that:')
    .setChoiceValues([
      'Too short',
      'About right',
      'Too long'
    ]);

  form.addParagraphTextItem()
    .setTitle('Anything else you\'d like to share about the Kick-Off presentations?');

  // ---- Section 4: Overall experience (everyone who participated) ----
  var overall = form.addPageBreakItem()
    .setTitle('Your Overall Experience');

  form.addMultipleChoiceItem()
    .setTitle('Overall, how would you rate the event?')
    .setChoiceValues([
      'Excellent',
      'Very good',
      'Good',
      'Fair',
      'Poor'
    ]);
  form.addParagraphTextItem()
    .setTitle('Any comments about your experience?');

  form.addMultipleChoiceItem()
    .setTitle('Did you receive the information you needed before the event?')
    .setChoiceValues([
      'Yes',
      'Mostly',
      'No'
    ]);

  form.addMultipleChoiceItem()
    .setTitle('The number of emails we sent before the event was:')
    .setChoiceValues([
      'Too many',
      'About right',
      'Too few'
    ]);
  form.addParagraphTextItem()
    .setTitle('Any comments about the information, emails, or their timing?');

  form.addMultipleChoiceItem()
    .setTitle('Regarding Early Check-in and T-Shirt Pick-up on September 19:')
    .setChoiceValues([
      'I attended and was satisfied with the service',
      'I attended and was dissatisfied with the service',
      'I didn\'t attend – I prefer checking in on the day of the event',
      'I would have liked to attend, but the date/time didn\'t work for me',
      'I didn\'t know early check-in was available'
    ]);
  form.addParagraphTextItem()
    .setTitle('Please share anything about early check-in that would help us.');

  // ---- Section 5: Last questions (everyone) ----
  var lastQuestions = form.addPageBreakItem()
    .setTitle('A Few Last Questions');

  form.addCheckboxItem()
    .setTitle('How did you hear about this event?')
    .setHelpText('Check all that apply.')
    .setChoiceValues([
      'I attended in previous years',
      'Word of mouth / invitation from family or friend',
      'LCSPTF email',
      'LCSPTF website',
      'Posted flyer',
      'Social media',
      'Church or faith community',
      'Organizational email or newsletter',
      'Radio',
      'Jeep Rally',
      'Other'
    ]);
  form.addParagraphTextItem()
    .setTitle('Please share details (where you saw a flyer, which social media or whose post, or other sources).');

  form.addMultipleChoiceItem()
    .setTitle('How likely are you to join us next year?')
    .setChoiceValues([
      'Very likely',
      'Somewhat likely',
      'Not sure',
      'Unlikely'
    ]);

  form.addParagraphTextItem()
    .setTitle('Your Final Thoughts')
    .setHelpText(
      'What did you like or dislike about the event? If you could change one thing, what would it be? ' +
      'Is there anything else you would like to share?'
    );

  // Send each person to the sections that fit how they took part.
  participation.setChoices([
    participation.createChoice('I attended the live event at the College of Lake County', atEvent),
    participation.createChoice('I walked/ran at a different place or time', overall),
    participation.createChoice('I watched via Facebook Live', kickOff),
    participation.createChoice('I planned to attend, but couldn\'t participate due to unexpected reasons', lastQuestions),
    participation.createChoice('I registered to support LCSPTF, but didn\'t plan to attend', lastQuestions)
  ]);

  // Linked spreadsheet for responses.
  var sheet = SpreadsheetApp.create('LCSPTF Walk/Run Survey – Responses');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, sheet.getId());

  // Newer Google Forms start unpublished; publish if this account supports it.
  try {
    form.setPublished(true);
  } catch (e) {
    // Older behavior: forms are already accepting responses.
  }

  // File the form and spreadsheet in the Walk Shared Folder.
  var filed = false;
  try {
    var folder = DriveApp.getFolderById(WALK_SHARED_FOLDER_ID);
    DriveApp.getFileById(form.getId()).moveTo(folder);
    DriveApp.getFileById(sheet.getId()).moveTo(folder);
    filed = true;
  } catch (e) {
    // This account can't reach the folder; the files stay in My Drive.
  }

  Logger.log('Share this link with participants: ' + form.getPublishedUrl());
  Logger.log('Edit the form here: ' + form.getEditUrl());
  Logger.log('Responses spreadsheet: ' + sheet.getUrl());
  Logger.log(filed
    ? 'Both files were saved in the Walk Shared Folder.'
    : 'Could not reach the Walk Shared Folder, so both files are in My Drive. Move them there by hand.');
}
