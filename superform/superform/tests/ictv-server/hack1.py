

class Hack(ICTVAuthPage):
    def GET(self, channel_id):
        chan = PluginChannel.get(channel_id)
        self.plugin_manager.add_mapping(self.app, chan)
        return

