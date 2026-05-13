import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:se_peav_mobile/main.dart';

void main() {
  testWidgets('App should render without errors', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(
      const ProviderScope(
        child: SEPeavApp(),
      ),
    );

    // Verify that the app renders
    expect(find.text('SE-PEAV'), findsOneWidget);
  });
}
