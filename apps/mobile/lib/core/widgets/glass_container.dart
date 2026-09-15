import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// Flat rounded card wrapper — the app's one shared "surface" primitive.
/// (Previously a frosted-glass/`BackdropFilter` treatment; dropped in favor
/// of flat opaque surfaces so light mode stays legible without a second set
/// of glass tokens.)
class GlassContainer extends StatelessWidget {
  final Widget child;
  final double borderRadius;
  final EdgeInsetsGeometry? padding;
  final EdgeInsetsGeometry? margin;
  final Color? color;
  final Border? border;
  final VoidCallback? onTap;

  const GlassContainer({
    super.key,
    required this.child,
    this.borderRadius = 20,
    this.padding,
    this.margin,
    this.color,
    this.border,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    Widget content = Container(
      padding: padding ?? const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color ?? colors.card,
        borderRadius: BorderRadius.circular(borderRadius),
        border: border ?? Border.all(color: colors.cardBorder, width: 1.0),
      ),
      child: child,
    );

    if (onTap != null) {
      content = Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(borderRadius),
          onTap: onTap,
          child: content,
        ),
      );
    }

    return Container(
      margin: margin,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(borderRadius),
        child: content,
      ),
    );
  }
}
