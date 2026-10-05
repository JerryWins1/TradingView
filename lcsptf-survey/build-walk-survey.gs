/**
 * Builds the LCSPTF 14th Annual Suicide Prevention & Awareness Walk/Run
 * participant survey as a Google Form, plus a linked Google Sheet for responses.
 *
 * How to use:
 *   1. Go to https://script.google.com and click "New project".
 *   2. Delete the sample code, paste this whole file in, and click Save.
 *   3. Click "Run" (with buildWalkSurvey selected) and approve the permissions.
 *   4. Open "Execution log" to find the links to your new form and sheet.
 */
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
  form.setProgressBar(false);

  // 1
  form.addMultipleChoiceItem()
    .setTitle('1. How did you participate in this year\'s event?')
    .setChoiceValues([
      'I attended the live event at the College of Lake County',
      'I walked/ran at a different place or time',
      'I watched via Facebook Live',
      'I planned to attend, but couldn\'t participate due to unexpected reasons',
      'I registered to support LCSPTF, but didn\'t plan to attend'
    ]);

  // 2
  form.addMultipleChoiceItem()
    .setTitle('2. Overall, how would you rate the event?')
    .setChoiceValues([
      'Excellent',
      'Very good',
      'Good',
      'Fair',
      'Poor',
      'Doesn\'t apply – I didn\'t participate'
    ]);
  form.addParagraphTextItem()
    .setTitle('Any comments about your experience?');

  // 3
  form.addMultipleChoiceItem()
    .setTitle('3. Before the event, which best describes the information and emails you received?')
    .setChoiceValues([
      'I had the information I needed, and the number of emails was about right',
      'I had the information I needed, but there were too many emails',
      'I had the information I needed, but would have liked more reminders',
      'I was missing information I needed'
    ]);
  form.addParagraphTextItem()
    .setTitle('Any comments about the information, emails, or their timing?');

  // 4
  form.addMultipleChoiceItem()
    .setTitle('4. Regarding Early Check-in and T-Shirt Pick-up on September 19:')
    .setChoiceValues([
      'I attended and was satisfied with the service',
      'I attended and was dissatisfied with the service',
      'I didn\'t attend – I prefer checking in on the day of the event',
      'I would have liked to attend, but the date/time didn\'t work for me',
      'I didn\'t know early check-in was available'
    ]);
  form.addParagraphTextItem()
    .setTitle('Please share anything about early check-in that would help us.');

  // 5
  form.addCheckboxItem()
    .setTitle('5. Resource Tables and Food Trucks')
    .setHelpText('Check all that apply.')
    .setChoiceValues([
      'I visited the resource tables and found them helpful',
      'I visited the resource tables but didn\'t find them helpful',
      'I didn\'t visit the resource tables',
      'I appreciated having the food trucks',
      'I\'d prefer not to have food trucks',
      'I didn\'t attend in person'
    ]);
  form.addParagraphTextItem()
    .setTitle('Any comments about the resource tables or food trucks?');

  // 6
  form.addMultipleChoiceItem()
    .setTitle('6. Regarding the Venue:')
    .setChoiceValues([
      'I like having the event at CLC',
      'I\'d prefer a different venue next year',
      'No preference',
      'I didn\'t attend in person'
    ]);
  form.addParagraphTextItem()
    .setTitle('Any comments about the venue or course, including suggestions for other locations or areas of the county?');

  // 7
  form.addCheckboxItem()
    .setTitle('7. Regarding the Kick-Off and Presentations (10:00–10:30)')
    .setHelpText('Check all that apply.')
    .setChoiceValues([
      'I appreciated the speakers and hearing their stories',
      'I was able to see and hear the presentations well',
      'I had difficulty seeing or hearing the presentations',
      'Half an hour felt about right',
      'Half an hour felt too long',
      'Half an hour felt too short',
      'I chose not to listen / arrived after the presentations',
      'I didn\'t attend or watch the Kick-Off'
    ]);
  form.addParagraphTextItem()
    .setTitle('Anything else you\'d like to share about the Kick-Off presentations?');

  // 8
  form.addCheckboxItem()
    .setTitle('8. How did you hear about this event?')
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

  // 9
  form.addParagraphTextItem()
    .setTitle('9. Your Final Thoughts')
    .setHelpText(
      'What did you like or dislike about the event? If you could change one thing, what would it be? ' +
      'Is there anything else you would like to share?'
    );

  // Linked spreadsheet for responses.
  var sheet = SpreadsheetApp.create('LCSPTF Walk/Run Survey – Responses');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, sheet.getId());

  // Newer Google Forms start unpublished; publish if this account supports it.
  try {
    form.setPublished(true);
  } catch (e) {
    // Older behavior: forms are already accepting responses.
  }

  Logger.log('Share this link with participants: ' + form.getPublishedUrl());
  Logger.log('Edit the form here: ' + form.getEditUrl());
  Logger.log('Responses spreadsheet: ' + sheet.getUrl());
}
