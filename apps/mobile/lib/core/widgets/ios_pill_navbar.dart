import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../theme/app_theme.dart';

class IOSPillNavItem {
  final IconData icon;
  final IconData activeIcon;
  final String label;

  const IOSPillNavItem({
    required this.icon,
    required this.activeIcon,
    required this.label,
  });
}

/// Floating pill bottom navigation bar. The "+" add action lives on
/// [Scaffold.floatingActionButton] instead of inside this bar.
class IOSPillNavBar extends StatelessWidget {
  final int currentIndex;
  final ValueChanged<int> onTap;
  final List<IOSPillNavItem> items;

  const IOSPillNavBar({
    super.key,
    required this.currentIndex,
    required this.onTap,
    required this.items,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final bottomPadding = MediaQuery.of(context).padding.bottom;
    final safeBottom = bottomPadding > 0 ? bottomPadding : 12.0;

    return Padding(
      padding: EdgeInsets.only(left: 16, right: 16, bottom: safeBottom),
      child: Container(
        height: 66,
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
        decoration: BoxDecoration(
          color: colors.surface,
          borderRadius: BorderRadius.circular(30),
          border: Border.all(color: colors.cardBorder, width: 1),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.12),
              blurRadius: 24,
              offset: const Offset(0, 8),
            ),
          ],
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            for (int i = 0; i < items.length; i++) _buildNavItem(context, i),
          ],
        ),
      ),
    );
  }

  Widget _buildNavItem(BuildContext context, int index) {
    final colors = context.colors;
    final item = items[index];
    final isSelected = index == currentIndex;

    return Expanded(
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: () {
          HapticFeedback.lightImpact();
          onTap(index);
        },
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 220),
          curve: Curves.easeOutCubic,
          padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 4),
          decoration: BoxDecoration(
            color: isSelected ? colors.accent.withValues(alpha: 0.12) : null,
            borderRadius: BorderRadius.circular(20),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                isSelected ? item.activeIcon : item.icon,
                color: isSelected ? colors.accent : colors.textMuted,
                size: 22,
              ),
              const SizedBox(height: 3),
              Text(
                item.label,
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                  color: isSelected ? colors.textPrimary : colors.textMuted,
                  letterSpacing: -0.2,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
