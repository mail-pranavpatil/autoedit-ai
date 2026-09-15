import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import 'glass_container.dart';

/// Consolidated icon + title + message (+ optional action) empty/error
/// state, replacing the 4 near-duplicate hand-rolled blocks across the
/// Home/Videos/Goals tabs.
class EmptyState extends StatelessWidget {
  final IconData icon;
  final String title;
  final String message;
  final String? actionLabel;
  final VoidCallback? onAction;
  final Color? iconColor;

  const EmptyState({
    super.key,
    required this.icon,
    required this.title,
    required this.message,
    this.actionLabel,
    this.onAction,
    this.iconColor,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return GlassContainer(
      padding: const EdgeInsets.all(20),
      borderRadius: 18,
      child: Column(
        children: [
          Icon(icon, color: iconColor ?? colors.accent, size: 34),
          const SizedBox(height: 10),
          Text(
            title,
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: colors.textPrimary),
          ),
          const SizedBox(height: 4),
          Text(
            message,
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 13, color: colors.textSecondary, height: 1.4),
          ),
          if (actionLabel != null && onAction != null) ...[
            const SizedBox(height: 16),
            ElevatedButton(onPressed: onAction, child: Text(actionLabel!)),
          ],
        ],
      ),
    );
  }
}
