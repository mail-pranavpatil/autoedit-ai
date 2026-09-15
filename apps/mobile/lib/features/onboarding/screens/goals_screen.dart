import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../core/api/api_client.dart';
import '../../../core/theme/app_theme.dart';
import '../models/onboarding_models.dart';
import 'experience_screen.dart';

class GoalsScreen extends StatefulWidget {
  final List<YouTubeChannel> channels;

  const GoalsScreen({super.key, required this.channels});

  @override
  State<GoalsScreen> createState() => _GoalsScreenState();
}

class _GoalsScreenState extends State<GoalsScreen> {
  int _activeChannelIndex = 0;
  late final Map<String, ChannelGoal> _goalsMap;

  final _viewsController = TextEditingController();
  final _subsController = TextEditingController();

  final List<int> _viewPresets = [25000, 50000, 100000, 500000, 1000000];
  final List<int> _subPresets = [1000, 5000, 10000, 50000, 100000];

  @override
  void initState() {
    super.initState();
    _goalsMap = {};
    final defaultDate = DateTime.now().add(const Duration(days: 90));

    for (final ch in widget.channels) {
      _goalsMap[ch.id] = ChannelGoal(
        channelId: ch.id,
        channelTitle: ch.title,
        targetViews: 50000,
        targetSubs: 10000,
        targetDate: defaultDate,
      );
    }
    _syncControllers();
  }

  void _syncControllers() {
    final currentChannel = widget.channels[_activeChannelIndex];
    final goal = _goalsMap[currentChannel.id]!;
    _viewsController.text = goal.targetViews.toString();
    _subsController.text = goal.targetSubs.toString();
  }

  @override
  void dispose() {
    _viewsController.dispose();
    _subsController.dispose();
    super.dispose();
  }

  Future<void> _pickDeadlineDate(ChannelGoal goal) async {
    final colors = context.colors;
    final picked = await showDatePicker(
      context: context,
      initialDate: goal.targetDate,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365 * 5)),
      builder: (context, child) {
        final baseTheme = Theme.of(context);
        return Theme(
          data: baseTheme.copyWith(
            colorScheme: baseTheme.colorScheme.copyWith(
              primary: colors.accent,
              surface: colors.card,
              onSurface: colors.textPrimary,
            ),
          ),
          child: child!,
        );
      },
    );

    if (picked != null) {
      setState(() {
        goal.targetDate = picked;
      });
    }
  }

  void _setDatePreset(ChannelGoal goal, int months) {
    setState(() {
      goal.targetDate = DateTime.now().add(Duration(days: months * 30));
    });
  }

  Future<void> _proceedToExperience() async {
    OnboardingState.instance.channelGoals = _goalsMap;

    // Persist goals to backend for each channel
    for (final entry in _goalsMap.entries) {
      try {
        await ApiClient.put(
          '/api/channels/${entry.key}/goals',
          body: entry.value.toJson(),
        );
      } catch (_) {}
    }

    if (!mounted) return;
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const ExperienceScreen()),
    );
  }

  String _formatNumber(int number) {
    if (number >= 1000000) {
      return '${(number / 1000000).toStringAsFixed(1)}M';
    }
    if (number >= 1000) {
      return '${(number / 1000).toStringAsFixed(0)}K';
    }
    return number.toString();
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final currentChannel = widget.channels[_activeChannelIndex];
    final currentGoal = _goalsMap[currentChannel.id]!;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: AppBar(
        title: const Text('Channel Goals'),
        leading: IconButton(
          icon: const Icon(CupertinoIcons.back),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Progress Bar (Step 3 of 5)
              Row(
                children: List.generate(5, (index) {
                  return Expanded(
                    child: Container(
                      height: 4,
                      margin: EdgeInsets.only(right: index < 4 ? 6 : 0),
                      decoration: BoxDecoration(
                        color: index <= 2 ? colors.accent : colors.cardBorder,
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  );
                }),
              ),
              const SizedBox(height: 20),

              // Channel Switcher if multiple channels
              if (widget.channels.length > 1) ...[
                SizedBox(
                  height: 40,
                  child: ListView.separated(
                    scrollDirection: Axis.horizontal,
                    itemCount: widget.channels.length,
                    separatorBuilder: (_, _) => const SizedBox(width: 8),
                    itemBuilder: (context, idx) {
                      final ch = widget.channels[idx];
                      final isActive = idx == _activeChannelIndex;
                      return ChoiceChip(
                        label: Text(ch.title),
                        selected: isActive,
                        selectedColor: colors.accent,
                        backgroundColor: colors.card,
                        labelStyle: TextStyle(
                          color: isActive ? Colors.white : colors.textSecondary,
                          fontWeight: isActive ? FontWeight.bold : FontWeight.normal,
                        ),
                        onSelected: (_) {
                          setState(() {
                            _activeChannelIndex = idx;
                            _syncControllers();
                          });
                        },
                      );
                    },
                  ),
                ),
                const SizedBox(height: 14),
              ],

              Text(
                'Goals for ${currentChannel.title}',
                style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                  color: colors.textPrimary,
                  letterSpacing: -0.4,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                'How many views & subscribers are you targeting, and by when?',
                style: TextStyle(
                  fontSize: 14,
                  color: colors.textSecondary,
                ),
              ),
              const SizedBox(height: 20),

              Expanded(
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // Views Goal Card
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: colors.card,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: colors.cardBorder),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Icon(CupertinoIcons.eye_fill, color: colors.accent, size: 20),
                                const SizedBox(width: 8),
                                Text(
                                  'Target Views',
                                  style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.bold,
                                    color: colors.textPrimary,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            Wrap(
                              spacing: 8,
                              children: _viewPresets.map((preset) {
                                final isSelected = currentGoal.targetViews == preset;
                                return ActionChip(
                                  label: Text('${_formatNumber(preset)} views'),
                                  backgroundColor: isSelected
                                      ? colors.accent.withValues(alpha: 0.2)
                                      : colors.surface,
                                  side: BorderSide(
                                    color: isSelected ? colors.accent : colors.cardBorder,
                                  ),
                                  labelStyle: TextStyle(
                                    color: isSelected ? colors.accent : colors.textSecondary,
                                    fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                                    fontSize: 12,
                                  ),
                                  onPressed: () {
                                    setState(() {
                                      currentGoal.targetViews = preset;
                                      _viewsController.text = preset.toString();
                                    });
                                  },
                                );
                              }).toList(),
                            ),
                            const SizedBox(height: 10),
                            TextFormField(
                              controller: _viewsController,
                              keyboardType: TextInputType.number,
                              style: TextStyle(color: colors.textPrimary),
                              decoration: const InputDecoration(
                                labelText: 'Custom Views Target',
                                hintText: 'e.g. 75000',
                              ),
                              onChanged: (val) {
                                final parsed = int.tryParse(val);
                                if (parsed != null) {
                                  setState(() => currentGoal.targetViews = parsed);
                                }
                              },
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Subscribers Goal Card
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: colors.card,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: colors.cardBorder),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Icon(CupertinoIcons.person_2_fill, color: colors.accent, size: 20),
                                const SizedBox(width: 8),
                                Text(
                                  'Target Subscribers',
                                  style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.bold,
                                    color: colors.textPrimary,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            Wrap(
                              spacing: 8,
                              children: _subPresets.map((preset) {
                                final isSelected = currentGoal.targetSubs == preset;
                                return ActionChip(
                                  label: Text('${_formatNumber(preset)} subs'),
                                  backgroundColor: isSelected
                                      ? colors.accent.withValues(alpha: 0.2)
                                      : colors.surface,
                                  side: BorderSide(
                                    color: isSelected ? colors.accent : colors.cardBorder,
                                  ),
                                  labelStyle: TextStyle(
                                    color: isSelected ? colors.accent : colors.textSecondary,
                                    fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                                    fontSize: 12,
                                  ),
                                  onPressed: () {
                                    setState(() {
                                      currentGoal.targetSubs = preset;
                                      _subsController.text = preset.toString();
                                    });
                                  },
                                );
                              }).toList(),
                            ),
                            const SizedBox(height: 10),
                            TextFormField(
                              controller: _subsController,
                              keyboardType: TextInputType.number,
                              style: TextStyle(color: colors.textPrimary),
                              decoration: const InputDecoration(
                                labelText: 'Custom Subscriber Target',
                                hintText: 'e.g. 15000',
                              ),
                              onChanged: (val) {
                                final parsed = int.tryParse(val);
                                if (parsed != null) {
                                  setState(() => currentGoal.targetSubs = parsed);
                                }
                              },
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Target Deadline Date Card
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: colors.card,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: colors.cardBorder),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Icon(CupertinoIcons.calendar, color: colors.warning, size: 20),
                                const SizedBox(width: 8),
                                Text(
                                  'Until Which Date?',
                                  style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.bold,
                                    color: colors.textPrimary,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            Row(
                              children: [
                                ActionChip(
                                  label: const Text('3 Months'),
                                  onPressed: () => _setDatePreset(currentGoal, 3),
                                ),
                                const SizedBox(width: 6),
                                ActionChip(
                                  label: const Text('6 Months'),
                                  onPressed: () => _setDatePreset(currentGoal, 6),
                                ),
                                const SizedBox(width: 6),
                                ActionChip(
                                  label: const Text('1 Year'),
                                  onPressed: () => _setDatePreset(currentGoal, 12),
                                ),
                              ],
                            ),
                            const SizedBox(height: 10),
                            InkWell(
                              borderRadius: BorderRadius.circular(12),
                              onTap: () => _pickDeadlineDate(currentGoal),
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                                decoration: BoxDecoration(
                                  color: colors.surface,
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(color: colors.cardBorder),
                                ),
                                child: Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text(
                                      DateFormat('MMMM dd, yyyy').format(currentGoal.targetDate),
                                      style: TextStyle(
                                        color: colors.textPrimary,
                                        fontSize: 15,
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                    Icon(CupertinoIcons.calendar_today,
                                        color: colors.accent, size: 20),
                                  ],
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],
                  ),
                ),
              ),

              ElevatedButton(
                onPressed: _proceedToExperience,
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text('Continue to Editing Experience'),
                    SizedBox(width: 8),
                    Icon(CupertinoIcons.arrow_right, size: 18),
                  ],
                ),
              ),
              const SizedBox(height: 8),
            ],
          ),
        ),
      ),
    );
  }
}
