import 'package:flutter/material.dart';

/// Pixel-perfect vector rendering of the official 4-color Google "G" logo.
class GoogleLogo extends StatelessWidget {
  final double size;
  const GoogleLogo({super.key, this.size = 20});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: CustomPaint(
        size: Size(size, size),
        painter: const _GoogleLogoPainter(),
      ),
    );
  }
}

class _GoogleLogoPainter extends CustomPainter {
  const _GoogleLogoPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final double s = size.width / 24.0;

    final paintBlue = Paint()
      ..color = const Color(0xFF4285F4)
      ..style = PaintingStyle.fill
      ..isAntiAlias = true;

    final paintGreen = Paint()
      ..color = const Color(0xFF34A853)
      ..style = PaintingStyle.fill
      ..isAntiAlias = true;

    final paintYellow = Paint()
      ..color = const Color(0xFFFBBC05)
      ..style = PaintingStyle.fill
      ..isAntiAlias = true;

    final paintRed = Paint()
      ..color = const Color(0xFFEA4335)
      ..style = PaintingStyle.fill
      ..isAntiAlias = true;

    // Blue section (Right bar & arc)
    final pathBlue = Path()
      ..moveTo(s * 23.745, s * 12.27)
      ..cubicTo(s * 23.745, s * 11.57, s * 23.685, s * 10.87, s * 23.555, s * 10.2)
      ..lineTo(s * 12.0, s * 10.2)
      ..lineTo(s * 12.0, s * 14.71)
      ..lineTo(s * 18.6, s * 14.71)
      ..cubicTo(s * 18.31, s * 16.23, s * 17.46, s * 17.53, s * 16.2, s * 18.39)
      ..lineTo(s * 16.2, s * 21.44)
      ..lineTo(s * 20.08, s * 21.44)
      ..cubicTo(s * 22.35, s * 19.35, s * 23.74, s * 16.27, s * 23.74, s * 12.27)
      ..close();
    canvas.drawPath(pathBlue, paintBlue);

    // Green section (Bottom arc)
    final pathGreen = Path()
      ..moveTo(s * 12.0, s * 24.0)
      ..cubicTo(s * 15.24, s * 24.0, s * 17.95, s * 22.92, s * 19.93, s * 21.09)
      ..lineTo(s * 16.05, s * 18.04)
      ..cubicTo(s * 14.97, s * 18.76, s * 13.6, s * 19.2, s * 12.0, s * 19.2)
      ..cubicTo(s * 8.88, s * 19.2, s * 6.23, s * 17.1, s * 5.28, s * 14.27)
      ..lineTo(s * 1.25, s * 14.27)
      ..lineTo(s * 1.25, s * 17.42)
      ..cubicTo(s * 3.26, s * 21.36, s * 7.33, s * 24.0, s * 12.0, s * 24.0)
      ..close();
    canvas.drawPath(pathGreen, paintGreen);

    // Yellow section (Left-bottom arc)
    final pathYellow = Path()
      ..moveTo(s * 5.28, s * 14.27)
      ..cubicTo(s * 5.03, s * 13.55, s * 4.9, s * 12.78, s * 4.9, s * 12.0)
      ..cubicTo(s * 4.9, s * 11.22, s * 5.03, s * 10.45, s * 5.28, s * 9.73)
      ..lineTo(s * 5.28, s * 6.58)
      ..lineTo(s * 1.25, s * 6.58)
      ..cubicTo(s * 0.45, s * 8.16, 0.0, s * 9.94, 0.0, s * 12.0)
      ..cubicTo(0.0, s * 14.06, s * 0.45, s * 15.84, s * 1.25, s * 17.42)
      ..lineTo(s * 5.28, s * 14.27)
      ..close();
    canvas.drawPath(pathYellow, paintYellow);

    // Red section (Top arc)
    final pathRed = Path()
      ..moveTo(s * 12.0, s * 4.75)
      ..cubicTo(s * 13.77, s * 4.75, s * 15.35, s * 5.36, s * 16.6, s * 6.55)
      ..lineTo(s * 20.02, s * 3.13)
      ..cubicTo(s * 17.95, s * 1.19, s * 15.24, 0.0, s * 12.0, 0.0)
      ..cubicTo(s * 7.33, 0.0, s * 3.26, s * 2.64, s * 1.25, s * 6.58)
      ..lineTo(s * 5.28, s * 9.73)
      ..cubicTo(s * 6.23, s * 6.9, s * 8.88, s * 4.8, s * 12.0, s * 4.8)
      ..close();
    canvas.drawPath(pathRed, paintRed);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
