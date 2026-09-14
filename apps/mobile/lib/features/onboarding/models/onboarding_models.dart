class SocialPlatform {
  final String id;
  final String name;
  final String icon;
  final bool isAvailable;
  bool isSelected;

  SocialPlatform({
    required this.id,
    required this.name,
    required this.icon,
    required this.isAvailable,
    this.isSelected = false,
  });
}

class YouTubeChannel {
  final String id;
  final String title;
  final String? avatarUrl;
  final String? subscriberCount;
  bool isSelected;

  YouTubeChannel({
    required this.id,
    required this.title,
    this.avatarUrl,
    this.subscriberCount,
    this.isSelected = true,
  });

  Map<String, dynamic> toJson() => {
        'channel_id': id,
        'channel_title': title,
        'thumbnail_url': avatarUrl,
      };
}

class ChannelGoal {
  final String channelId;
  final String channelTitle;
  int targetViews;
  int targetSubs;
  DateTime targetDate;

  ChannelGoal({
    required this.channelId,
    required this.channelTitle,
    this.targetViews = 50000,
    this.targetSubs = 10000,
    required this.targetDate,
  });

  Map<String, dynamic> toJson() => {
        'target_views': targetViews,
        'target_subs': targetSubs,
        'target_date': targetDate.toIso8601String().split('T')[0],
      };
}

enum EditingExperience {
  noob('noob', 'Noob', 'Never edited before', 'I want AI to automate everything from raw footage to final video.'),
  rookie('rookie', 'Rookie', 'Made a few clips', 'I know basic cuts and transitions, but editing takes too long.'),
  pro('pro', 'Pro', 'Experienced Creator', 'I know Premiere / DaVinci and need maximum speed & high-converting automation.');

  final String key;
  final String title;
  final String subtitle;
  final String description;

  const EditingExperience(this.key, this.title, this.subtitle, this.description);
}

class OnboardingState {
  static final OnboardingState instance = OnboardingState._();
  OnboardingState._();

  List<YouTubeChannel> selectedChannels = [];
  Map<String, ChannelGoal> channelGoals = {};
  EditingExperience? experience;
  String? creationReason;

  void reset() {
    selectedChannels.clear();
    channelGoals.clear();
    experience = null;
    creationReason = null;
  }
}
