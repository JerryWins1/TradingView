/**
 * Makes "Version A" of the Walk/Run Participant Survey for the group to
 * compare. The current survey is left untouched; this script copies it,
 * adds an "At the Event" section (resource tables, food trucks, Kick-Off
 * presentations) that only CLC attendees see, and gives the copy its own
 * responses spreadsheet. Both files are saved in the Walk Shared Folder.
 *
 * How to use:
 *   1. Open your Apps Script project and replace the code with this file.
 *   2. Click Save, choose makeVersionA next to Debug, and click Run.
 *   3. Open "Execution log" to find the links to Version A.
 */

// The current survey (left as it is).
var ORIGINAL_FORM_ID = '1ouS31Zn_gFxguCWxo2L--SKDT89J3H4PQN5eeJxcgRo';

// The Task Force's "Walk Shared Folder" in Google Drive.
var WALK_SHARED_FOLDER_ID = '1T_Xxe4e6NEagLJ6gYW8v07hXoecI-8aX';

var VERSION_SUFFIX = ' – A';

function makeVersionA() {
  var folder = DriveApp.getFolderById(WALK_SHARED_FOLDER_ID);
  var original = DriveApp.getFileById(ORIGINAL_FORM_ID);
  var copy = original.makeCopy(original.getName() + VERSION_SUFFIX, folder);
  var form = FormApp.openById(copy.getId());
  form.setTitle(form.getTitle() + VERSION_SUFFIX);

  var takePart = findItem(form, FormApp.ItemType.MULTIPLE_CHOICE, 'How did you take part this year?')
    .asMultipleChoiceItem();
  var experience = findItem(form, FormApp.ItemType.PAGE_BREAK, 'Your Experience').asPageBreakItem();
  var lastQuestions = findItem(form, FormApp.ItemType.PAGE_BREAK, 'A Few Last Questions').asPageBreakItem();

  // ---- New section: At the Event (CLC attendees only) ----
  var atEvent = form.addPageBreakItem()
    .setTitle('At the Event');

  var resourceTables = form.addMultipleChoiceItem()
    .setTitle('Regarding the Resource Tables:')
    .setChoiceValues([
      'I visited them and found them helpful',
      'I visited them, but they weren\'t very helpful',
      'I didn\'t visit them – I wasn\'t interested',
      'I didn\'t visit them – I didn\'t have time',
      'I didn\'t know there were resource tables'
    ]);

  var resourceComment = form.addParagraphTextItem()
    .setTitle('Which resources were most helpful, or what would you like to see added?');

  var foodTrucks = form.addMultipleChoiceItem()
    .setTitle('Regarding the Food Trucks:')
    .setChoiceValues([
      'I appreciated having the food trucks',
      'I didn\'t use them, but it\'s nice to have them',
      'I\'d prefer not to have food trucks'
    ]);

  var presentations = form.addCheckboxItem()
    .setTitle('Regarding the Kick-Off and Presentations:')
    .setHelpText('Check any that apply.')
    .setChoiceValues([
      'I appreciated the speakers and hearing their stories',
      'I could see and hear the presentations well',
      'I had trouble seeing or hearing the presentations',
      'I chose not to listen to the presentations',
      'I arrived after the presentations'
    ]);

  // Place the new section right after the first question.
  var newItems = [atEvent, resourceTables, resourceComment, foodTrucks, presentations];
  var position = takePart.getIndex() + 1;
  newItems.forEach(function (item) {
    form.moveItem(item.getIndex(), position);
    position++;
  });

  // CLC attendees see the new section; everyone else skips it as before.
  takePart.setChoices([
    takePart.createChoice('At the College of Lake County', atEvent),
    takePart.createChoice('I walked/ran on my own, somewhere else', experience),
    takePart.createChoice('I watched on Facebook Live', experience),
    takePart.createChoice('I couldn\'t make it this year', lastQuestions)
  ]);

  // Version A gets its own responses spreadsheet.
  var sheet = SpreadsheetApp.create(copy.getName() + ' – Responses');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, sheet.getId());
  DriveApp.getFileById(sheet.getId()).moveTo(folder);

  try {
    form.setPublished(true);
  } catch (e) {
    // Older behavior: forms are already accepting responses.
  }

  Logger.log('Version A survey link: ' + form.getPublishedUrl());
  Logger.log('Edit Version A here: ' + form.getEditUrl());
  Logger.log('Version A responses: ' + sheet.getUrl());
  Logger.log('Both files were saved in the Walk Shared Folder. The original survey was not changed.');
}

function findItem(form, type, title) {
  var items = form.getItems(type);
  for (var i = 0; i < items.length; i++) {
    if (items[i].getTitle() === title) {
      return items[i];
    }
  }
  throw new Error('Could not find "' + title + '" in the survey. Has it been renamed?');
}
