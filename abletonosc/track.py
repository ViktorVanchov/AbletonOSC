from typing import Tuple, Any, Callable, Optional
from .handler import AbletonOSCHandler


class TrackHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "track"

    def init_api(self):
        def create_track_callback(func: Callable,
                                  *args,
                                  include_track_id: bool = False):
            def track_callback(params: Tuple[Any]):
                if params[0] == "*":
                    track_indices = list(range(len(self.song.tracks)))
                else:
                    track_indices = [int(params[0])]

                for track_index in track_indices:
                    self.logger.info(f"Logs:{[self.song.tracks + self.song.return_tracks + (self.song.master_track,)]}")
                    track = [self.song.tracks + self.song.return_tracks + (self.song.master_track,)][0][track_index]
                    if include_track_id:
                        rv = func(track, *args, tuple([track_index] + params[1:]))
                    else:
                        rv = func(track, *args, tuple(params[1:]))

                    if rv is not None:
                        return (track_index, *rv)

            return track_callback

        methods = [
            "delete_device",
            "stop_all_clips"
        ]
        properties_r = [
            "can_be_armed",
            "fired_slot_index",
            "has_audio_input",
            "has_audio_output",
            "has_midi_input",
            "has_midi_output",
            "is_foldable",
            "is_grouped",
            "is_visible",
            "output_meter_level",
            "output_meter_left",
            "output_meter_right",
            "playing_slot_index",
        ]
        properties_rw = [
            "arm",
            "color",
            "color_index",
            "current_monitoring_state",
            "fold_state",
            "mute",
            "solo",
            "name"
        ]

        for method in methods:
            self.osc_server.add_handler("/live/track/%s" % method,
                                        create_track_callback(self._call_method, method))

        for prop in properties_r + properties_rw:
            self.osc_server.add_handler("/live/track/get/%s" % prop,
                                        create_track_callback(self._get_property, prop))
            self.osc_server.add_handler("/live/track/start_listen/%s" % prop,
                                        create_track_callback(self._start_listen, prop, include_track_id=True))
            self.osc_server.add_handler("/live/track/stop_listen/%s" % prop,
                                        create_track_callback(self._stop_listen, prop, include_track_id=True))
        for prop in properties_rw:
            self.osc_server.add_handler("/live/track/set/%s" % prop,
                                        create_track_callback(self._set_property, prop))

        #------------------Return track and Master Track calls------------------------
        def return_track_color(params):
            track_id = params[0]
            color = self.song.return_tracks[track_id].color
            # Return a properly structured tuple without nesting
            return (track_id, color)
        self.osc_server.add_handler("/live/return_track/get/color", return_track_color)

        def return_track_name(params):
            track_id = params[0]
            name = self.song.return_tracks[track_id].name
            
            # Check if name contains pipe separators and split it into a list
            if isinstance(name, str) and ' | ' in name:
                names = []
                for part in name.split(' | '):
                    names.append(part)  # Don't add quotes, they will be added by OSC serializer
                return (track_id, names)
            else:
                # Add quotes to the name
                if isinstance(name, str):
                    name = f"'{name}'"
                # Return a properly structured tuple without nesting
                return (track_id, name)
        self.osc_server.add_handler("/live/return_track/get/name", return_track_name)

        def return_track_color_index(params):
            track_id = params[0]
            color_index = self.song.return_tracks[track_id].color_index
            # Return a properly structured tuple without nesting
            return (track_id, color_index)
        self.osc_server.add_handler("/live/return_track/get/color_index", return_track_color_index)

        def return_track_devices_name(params):
            track_id = params[0]
            device_list = get_all_devices(self.song.return_tracks[track_id])
            device_names = []
            for device in device_list:
                # Check if device name contains pipe separators
                if ' | ' in device.name:
                    # Split at pipes and add each name separately
                    for name in device.name.split(' | '):
                        device_names.append(name)  # Don't add quotes
                else:
                    device_names.append(device.name)  # Don't add quotes
            # Return a properly structured tuple with the list of names
            return (track_id, device_names)
        self.osc_server.add_handler("/live/return_track/get/devices/name", return_track_devices_name)

        def return_track_devices_type(params):
            track_id = params[0]
            device_list = get_all_devices(self.song.return_tracks[track_id])
            # Use integers instead of strings for device types
            device_types = [int(x.type) for x in device_list if hasattr(x, "type")]
            # Return a properly structured tuple without nesting
            return (track_id, device_types)
        self.osc_server.add_handler("/live/return_track/get/devices/type", return_track_devices_type)

        def return_track_devices_class_name(params):
            track_id = params[0]
            device_list = get_all_devices(self.song.return_tracks[track_id])
            class_names = [x.class_name for x in device_list if hasattr(x, "class_name")]
            # Return a properly structured tuple without nesting
            return (track_id, class_names)
        self.osc_server.add_handler("/live/return_track/get/devices/class_name", return_track_devices_class_name)

        def return_track_numdevices(params):
            track_id = params[0]
            device_list = get_all_devices(self.song.return_tracks[track_id])
            count = len(device_list)
            # Return a properly structured tuple without nesting
            return (track_id, count)
        self.osc_server.add_handler("/live/return_track/get/num_devices", return_track_numdevices)

        def master_track_devices_num_devices(params):
            device_list = get_all_devices(self.song.master_track)
            self.logger.info(device_list)
            return (len(device_list),)
        self.osc_server.add_handler("/live/master_track/get/num_devices", master_track_devices_num_devices)

        def master_track_devices_name_devices(params):
            device_list = get_all_devices(self.song.master_track)
            # Return names with quotes around each name
            return tuple(f"'{x.name}'" for x in device_list)
        self.osc_server.add_handler("/live/master_track/get/devices/name", master_track_devices_name_devices)

        def master_track_devices_type_devices(params):
            device_list = get_all_devices(self.song.master_track)
            # Return device types as actual tuple elements
            return tuple(int(x.type) for x in device_list if hasattr(x, 'type'))
        self.osc_server.add_handler("/live/master_track/get/devices/type", master_track_devices_type_devices)

        def master_track_devices_class_name_devices(params):
            device_list = get_all_devices(self.song.master_track)
            # Return class names as actual tuple elements with quotes
            return tuple(f"'{x.class_name}'" for x in device_list if hasattr(x, "class_name"))
        self.osc_server.add_handler("/live/master_track/get/devices/class_name",
                                    master_track_devices_class_name_devices)

        def get_num_devices_racks_included(track, _):
            full_data = get_all_devices(track)
            return tuple([len(full_data)])

        self.osc_server.add_handler("/live/track/get/num_devices",
                                    create_track_callback(get_num_devices_racks_included))

        def device_get_parameters_name(track, _):
            device = get_all_devices(track)[_[0]]
            return tuple([_[0]]) + tuple([parameter.name for parameter in device.parameters])

        self.osc_server.add_handler("/live/device/get/parameters/name",
                                    create_track_callback(device_get_parameters_name))

        #--------------------------------------------------------------------------------
        # Volume, panning and send are properties of the track's mixer_device so
        # can't be formulated as normal callbacks that reference properties of track.
        #--------------------------------------------------------------------------------
        mixer_properties_rw = ["volume", "panning"]
        for prop in mixer_properties_rw:
            self.osc_server.add_handler("/live/track/get/%s" % prop,
                                        create_track_callback(self._get_mixer_property, prop))
            self.osc_server.add_handler("/live/track/set/%s" % prop,
                                        create_track_callback(self._set_mixer_property, prop))
            self.osc_server.add_handler("/live/track/start_listen/%s" % prop,
                                        create_track_callback(self._start_mixer_listen, prop, include_track_id=True))
            self.osc_server.add_handler("/live/track/stop_listen/%s" % prop,
                                        create_track_callback(self._stop_mixer_listen, prop, include_track_id=True))

        # Still need to fix these
        # Might want to find a better approach that unifies volume and sends
        def track_get_send(track, params: Tuple[Any] = ()):
            send_id, = params
            return send_id, track.mixer_device.sends[send_id].value

        def track_set_send(track, params: Tuple[Any] = ()):
            send_id, value = params
            track.mixer_device.sends[send_id].value = value

        self.osc_server.add_handler("/live/track/get/send", create_track_callback(track_get_send))
        self.osc_server.add_handler("/live/track/set/send", create_track_callback(track_set_send))

        def track_delete_clip(track, params: Tuple[Any]):
            clip_index, = params
            track.clip_slots[clip_index].delete_clip()

        self.osc_server.add_handler("/live/track/delete_clip", create_track_callback(track_delete_clip))

        def track_get_clip_names(track, _):
            return tuple(clip_slot.clip.name if clip_slot.clip else None for clip_slot in track.clip_slots)

        def track_get_clip_lengths(track, _):
            return tuple(clip_slot.clip.length if clip_slot.clip else None for clip_slot in track.clip_slots)

        def track_get_clip_colors(track, _):
            return tuple(clip_slot.clip.color if clip_slot.clip else None for clip_slot in track.clip_slots)

        def track_get_arrangement_clip_names(track, _):
            return tuple(clip.name for clip in track.arrangement_clips)

        def track_get_arrangement_clip_lengths(track, _):
            return tuple(clip.length for clip in track.arrangement_clips)

        def track_get_arrangement_clip_start_times(track, _):
            return tuple(clip.start_time for clip in track.arrangement_clips)

        """
        Returns a list of clip properties, or Nil if clip is empty
        """
        self.osc_server.add_handler("/live/track/get/clips/name", create_track_callback(track_get_clip_names))
        self.osc_server.add_handler("/live/track/get/clips/length", create_track_callback(track_get_clip_lengths))
        self.osc_server.add_handler("/live/track/get/clips/color", create_track_callback(track_get_clip_colors))
        self.osc_server.add_handler("/live/track/get/arrangement_clips/name", create_track_callback(track_get_arrangement_clip_names))
        self.osc_server.add_handler("/live/track/get/arrangement_clips/length", create_track_callback(track_get_arrangement_clip_lengths))
        self.osc_server.add_handler("/live/track/get/arrangement_clips/start_time", create_track_callback(track_get_arrangement_clip_start_times))

        def get_all_sub_rack_devices(rack):
            all_sub_devices = []
            for chain in rack.chains:
                for device in chain.devices:
                    if (str(type(device)) == "<class 'RackDevice.RackDevice'>"):
                        all_sub_devices.extend([device])
                        sub_devices = get_all_sub_rack_devices(device)
                        all_sub_devices.extend(sub_devices)
                    else:
                        all_sub_devices.extend([device])
            return all_sub_devices

        def convert_dict_to_list(dict):
            dict_list = list(dict.keys())[0]
            dict_values = list(dict.values())[0]
            return [dict_list] + dict_values

        def get_all_devices(track):
            full_data = []
            device_list = [x for x in track.devices]
            devices = []
            for device in device_list:
                if ("RackDevice" in str(type(device))):
                    rack = device
                    devices.clear()
                    for chain in rack.chains:
                        for device in chain.devices:
                            devices.append(device)
                            if ("RackDevice" in str(type(device))):
                                sub_devices = get_all_sub_rack_devices(device)
                                devices.extend(sub_devices)
                    all_devices_in_rack = {rack: devices}
                    full_data.extend(convert_dict_to_list(all_devices_in_rack))
                else:
                    full_data.append(device)
            return full_data

        def track_get_num_devices(track, _):
            return len(track.devices),

        def track_get_device_names(track, _):
            return tuple(device.name for device in track.devices)

        def track_get_device_types(track, _):
            return tuple(device.type for device in track.devices)

        def track_get_device_class_names(track, _):
            return tuple(device.class_name for device in track.devices)

        def track_get_device_can_have_chains(track, _):
            return tuple(device.can_have_chains for device in track.devices)

        def track_get_device_is_foldable(track, _):
            full_data = get_all_devices(track)
            return tuple([_[0], full_data[_[0]].can_have_chains])
        self.osc_server.add_handler("/live/device/get/is_foldable", create_track_callback(track_get_device_is_foldable))

        def track_get_device_rack_device_name(track, _):
            full_data = get_all_devices(track)
            name = full_data[_[0]].name
            # Add quotes to string values
            if isinstance(name, str):
                name = f"'{name}'"
            return tuple([_[0], name])
        self.osc_server.add_handler("/live/device/get/rack_device_name", create_track_callback(track_get_device_rack_device_name))

        def track_get_device_is_grouped(track, _):
            full_data = get_all_devices(track)
            if(str(type(full_data[_[0]].canonical_parent)) == "<class 'Chain.Chain'>"):#hasattr(full_data[_[0]].canonical_parent, 'chains')):
                return tuple([_[0], True])
            else:
                return tuple([_[0], False])
        self.osc_server.add_handler("/live/device/get/is_grouped", create_track_callback(track_get_device_is_grouped))

        def track_get_device_num_of_chains(track, _):
            full_data = get_all_devices(track)
            return tuple([_[0], len(full_data[_[0]].chains)])
        self.osc_server.add_handler("/live/device/get/number_of_chains", create_track_callback(track_get_device_num_of_chains))

        def track_get_device_name_of_chains(track, _):
            full_data = get_all_devices(track)
            chains_list = []
            # Process chain names for proper formatting
            for chain in full_data[_[0]].chains:
                # Check if chain name contains pipe separators
                if ' | ' in chain.name:
                    # Split at pipes and add each name separately
                    for name in chain.name.split(' | '):
                        chains_list.append(name)
                else:
                    chains_list.append(chain.name)
            # Return as tuple with device index and nested list to match format
            return tuple([_[0], [chains_list]])
        self.osc_server.add_handler("/live/device/get/names_of_chains", create_track_callback(track_get_device_name_of_chains))

        def track_get_device_name_of_devicechains(track, _):
            full_data = get_all_devices(track)
            return tuple([_[0], [x.name for x in full_data[_[0]:] if 'Device.Device' in (str(type(x))) and 'Chain' in str(type(x.canonical_parent))]])
        self.osc_server.add_handler("/live/device/get/names_of_devices_in_chain", create_track_callback(track_get_device_name_of_devicechains))

        def track_get_device_name_of_chain(track, _):
            full_data = get_all_devices(track)
            return tuple([_[0],[x.name for x in full_data if str(type(x)) == "<class 'RackDevice.RackDevice'>"][_[0]]])
        self.osc_server.add_handler("/live/device/get/chain_name", create_track_callback(track_get_device_name_of_chain))

        def get_device_location(track, _):
            full_data = get_all_devices(track)
            device_class = full_data[_[0]].class_name
            device_name = full_data[_[0]].name
            if(hasattr(full_data[_[0]],"is_foldable")):device_foldable = full_data[_[0]].is_foldable
            else: device_foldable = None
            if(hasattr(full_data[_[0]],"is_grouped")):device_grouped = full_data[_[0]].is_grouped
            else: device_grouped = None
            device_rack_name = full_data[_[0]].canonical_parent.name
            if(full_data[_[0]].can_have_chains): device_chain_name = full_data[_[0]].chains[0].name
            else:
                device_chain_name = None
                
            # Add quotes to string values directly in the function
            if isinstance(device_class, str):
                device_class = f"'{device_class}'"
            if isinstance(device_name, str):
                device_name = f"'{device_name}'"
            if isinstance(device_rack_name, str):
                device_rack_name = f"'{device_rack_name}'"
            if isinstance(device_chain_name, str):
                device_chain_name = f"'{device_chain_name}'"
                
            return tuple([_[0],device_class,device_name, device_foldable, device_grouped,device_rack_name,device_chain_name])
        self.osc_server.add_handler("/live/device/get/location", create_track_callback(get_device_location))

        def get_selected_device(track):
            full_data = get_all_devices(self.song.view.selected_track)
            selected_device_id = [i for i, x in enumerate(full_data) if(x == self.song.view.selected_track.view.selected_device)][0]
            all_tracks = list(self.song.tracks)
            all_tracks.extend(x for x in self.song.return_tracks)
            all_tracks.extend([self.song.master_track])
            selected_track_id = [i for i,x in enumerate(all_tracks) if(x == self.song.view.selected_track)][0]
            return tuple([selected_track_id,selected_device_id])
        self.osc_server.add_handler("/live/device/get/selected", get_selected_device)

        def device_get_name(track, _):
            full_data = get_all_devices(track)
            return tuple([full_data[_[0]].name])
        self.osc_server.add_handler("/live/device/get/name", create_track_callback(device_get_name))

        """
         - name: the device's human-readable name
         - type: 0 = audio_effect, 1 = instrument, 2 = midi_effect
         - class_name: e.g. Operator, Reverb, AuPluginDevice, PluginDevice, InstrumentGroupDevice
        """
        self.osc_server.add_handler("/live/track/get/num_devices", create_track_callback(track_get_num_devices))
        self.osc_server.add_handler("/live/track/get/devices/name", create_track_callback(track_get_device_names))
        self.osc_server.add_handler("/live/track/get/devices/type", create_track_callback(track_get_device_types))
        self.osc_server.add_handler("/live/track/get/devices/class_name", create_track_callback(track_get_device_class_names))
        self.osc_server.add_handler("/live/track/get/devices/can_have_chains", create_track_callback(track_get_device_can_have_chains))

        #--------------------------------------------------------------------------------
        # Track: Output routing.
        # An output route has a type (e.g. "Ext. Out") and a channel (e.g. "1/2").
        # Since Live 10, both of these need to be set by reference to the appropriate
        # item in the available_output_routing_types vector.
        #--------------------------------------------------------------------------------
        def track_get_available_output_routing_types(track, _):
            return tuple([routing_type.display_name for routing_type in track.available_output_routing_types])
        def track_get_available_output_routing_channels(track, _):
            return tuple([routing_channel.display_name for routing_channel in track.available_output_routing_channels])
        def track_get_output_routing_type(track, _):
            return track.output_routing_type.display_name,
        def track_set_output_routing_type(track, params):
            type_name = str(params[0])
            for routing_type in track.available_output_routing_types:
                if routing_type.display_name == type_name:
                    track.output_routing_type = routing_type
                    return
            self.logger.warning("Couldn't find output routing type: %s" % type_name)
        def track_get_output_routing_channel(track, _):
            return track.output_routing_channel.display_name,
        def track_set_output_routing_channel(track, params):
            channel_name = str(params[0])
            for channel in track.available_output_routing_channels:
                if channel.display_name == channel_name:
                    track.output_routing_channel = channel
                    return
            self.logger.warning("Couldn't find output routing channel: %s" % channel_name)

        self.osc_server.add_handler("/live/track/get/available_output_routing_types", create_track_callback(track_get_available_output_routing_types))
        self.osc_server.add_handler("/live/track/get/available_output_routing_channels", create_track_callback(track_get_available_output_routing_channels))
        self.osc_server.add_handler("/live/track/get/output_routing_type", create_track_callback(track_get_output_routing_type))
        self.osc_server.add_handler("/live/track/set/output_routing_type", create_track_callback(track_set_output_routing_type))
        self.osc_server.add_handler("/live/track/get/output_routing_channel", create_track_callback(track_get_output_routing_channel))
        self.osc_server.add_handler("/live/track/set/output_routing_channel", create_track_callback(track_set_output_routing_channel))

        #--------------------------------------------------------------------------------
        # Track: Input routing.
        #--------------------------------------------------------------------------------
        def track_get_available_input_routing_types(track, _):
            return tuple([routing_type.display_name for routing_type in track.available_input_routing_types])
        def track_get_available_input_routing_channels(track, _):
            return tuple([routing_channel.display_name for routing_channel in track.available_input_routing_channels])
        def track_get_input_routing_type(track, _):
            return track.input_routing_type.display_name,
        def track_set_input_routing_type(track, params):
            type_name = str(params[0])
            for routing_type in track.available_input_routing_types:
                if routing_type.display_name == type_name:
                    track.input_routing_type = routing_type
                    return
            self.logger.warning("Couldn't find input routing type: %s" % type_name)
        def track_get_input_routing_channel(track, _):
            return track.input_routing_channel.display_name,
        def track_set_input_routing_channel(track, params):
            channel_name = str(params[0])
            for channel in track.available_input_routing_channels:
                if channel.display_name == channel_name:
                    track.input_routing_channel = channel
                    return
            self.logger.warning("Couldn't find input routing channel: %s" % channel_name)

        self.osc_server.add_handler("/live/track/get/available_input_routing_types", create_track_callback(track_get_available_input_routing_types))
        self.osc_server.add_handler("/live/track/get/available_input_routing_channels", create_track_callback(track_get_available_input_routing_channels))
        self.osc_server.add_handler("/live/track/get/input_routing_type", create_track_callback(track_get_input_routing_type))
        self.osc_server.add_handler("/live/track/set/input_routing_type", create_track_callback(track_set_input_routing_type))
        self.osc_server.add_handler("/live/track/get/input_routing_channel", create_track_callback(track_get_input_routing_channel))
        self.osc_server.add_handler("/live/track/set/input_routing_channel", create_track_callback(track_set_input_routing_channel))

    def _set_mixer_property(self, target, prop, params: Tuple) -> None:
        parameter_object = getattr(target.mixer_device, prop)
        self.logger.info("Setting property for %s: %s (new value %s)" % (self.class_identifier, prop, params[0]))
        parameter_object.value = params[0]

    def _get_mixer_property(self, target, prop, params: Optional[Tuple] = ()) -> Tuple[Any]:
        parameter_object = getattr(target.mixer_device, prop)
        self.logger.info("Getting property for %s: %s = %s" % (self.class_identifier, prop, parameter_object.value))
        return parameter_object.value,

    def _start_mixer_listen(self, target, prop, params: Optional[Tuple] = ()) -> None:
        parameter_object = getattr(target.mixer_device, prop)
        def property_changed_callback():
            value = parameter_object.value
            self.logger.info("Property %s changed of %s %s: %s" % (prop, self.class_identifier, str(params), value))
            osc_address = "/live/%s/get/%s" % (self.class_identifier, prop)
            self.osc_server.send(osc_address, (*params, value,))

        listener_key = (prop, tuple(params))
        if listener_key in self.listener_functions:
            self._stop_mixer_listen(target, prop, params)

        self.logger.info("Adding listener for %s %s, property: %s" % (self.class_identifier, str(params), prop))

        parameter_object.add_value_listener(property_changed_callback)
        self.listener_functions[listener_key] = property_changed_callback
        #--------------------------------------------------------------------------------
        # Immediately send the current value
        #--------------------------------------------------------------------------------
        property_changed_callback()

    def _stop_mixer_listen(self, target, prop, params: Optional[Tuple[Any]] = ()) -> None:
        parameter_object = getattr(target.mixer_device, prop)
        listener_key = (prop, tuple(params))
        if listener_key in self.listener_functions:
            self.logger.info("Removing listener for %s %s, property %s" % (self.class_identifier, str(params), prop))
            listener_function = self.listener_functions[listener_key]
            parameter_object.remove_value_listener(listener_function)
            del self.listener_functions[listener_key]
        else:
            self.logger.warning("No listener function found for property: %s (%s)" % (prop, str(params)))
