import 'package:flutter_test/flutter_test.dart';

import 'package:autoedit_mobile/core/widgets/stage_labels.dart';

void main() {
  test('stageTitle maps known backend stages to friendly labels', () {
    expect(stageTitle('SEARCHING_BROLL'), 'Stock search');
    expect(stageTitle('READY'), 'Done');
    expect(stageTitle(null), '');
    expect(stageTitle('SOME_FUTURE_STAGE'), 'SOME_FUTURE_STAGE'); // falls back to the raw value
  });

  test('statusBucket groups raw statuses for badge coloring', () {
    expect(statusBucket('READY'), StatusBucket.ready);
    expect(statusBucket('FAILED'), StatusBucket.failed);
    expect(statusBucket('QUEUED'), StatusBucket.queued);
    expect(statusBucket('DISCOVERED'), StatusBucket.queued);
    expect(statusBucket(null), StatusBucket.queued);
    expect(statusBucket('RENDERING'), StatusBucket.processing);
  });
}
