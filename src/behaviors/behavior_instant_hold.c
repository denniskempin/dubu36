/*
 * Instant hold. The hold key goes down with the physical key. A release
 * inside the tapping term releases it and then taps the tap key. A longer
 * press leaves the hold key down until release.
 *
 * Other keys are not captured, so a shortcut key pressed while this is held
 * reaches the host immediately, with the hold key already down.
 *
 * Two keys that share a hold code (both F18 keys, or both F19 keys) keep
 * that code down while either is physically held. A quick release still
 * lifts the hold for the tap, then presses it again if the other key is
 * still down.
 *
 * SPDX-License-Identifier: MIT
 */

#define DT_DRV_COMPAT zmk_behavior_instant_hold

#include <zephyr/device.h>
#include <zephyr/logging/log.h>
#include <drivers/behavior.h>
#include <zmk/behavior.h>

#if DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT)

LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

#define IH_MAX_SLOTS 8
#define IH_POSITION_UNUSED -1

struct behavior_instant_hold_config {
    int32_t tapping_term_ms;
    const char *hold_behavior_dev;
    const char *tap_behavior_dev;
};

struct ih_slot {
    int32_t position;
    uint32_t hold;
    uint32_t tap;
    int64_t pressed_at;
#if IS_ENABLED(CONFIG_ZMK_SPLIT)
    uint8_t source;
#endif
};

struct behavior_instant_hold_data {
    struct ih_slot slots[IH_MAX_SLOTS];
#if IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)
    struct behavior_parameter_metadata_set set;
#endif
};

static int ih_init(const struct device *dev) {
    struct behavior_instant_hold_data *data = dev->data;

    for (int i = 0; i < IH_MAX_SLOTS; i++) {
        data->slots[i].position = IH_POSITION_UNUSED;
    }
    return 0;
}

static struct ih_slot *find_slot(struct behavior_instant_hold_data *data, int32_t position) {
    for (int i = 0; i < IH_MAX_SLOTS; i++) {
        if (data->slots[i].position == position) {
            return &data->slots[i];
        }
    }
    return NULL;
}

static struct ih_slot *alloc_slot(struct behavior_instant_hold_data *data) {
    return find_slot(data, IH_POSITION_UNUSED);
}

static int count_hold(struct behavior_instant_hold_data *data, uint32_t hold) {
    int count = 0;

    for (int i = 0; i < IH_MAX_SLOTS; i++) {
        if (data->slots[i].position != IH_POSITION_UNUSED && data->slots[i].hold == hold) {
            count++;
        }
    }
    return count;
}

static int send_key(const char *behavior_dev, uint32_t param, struct ih_slot *slot,
                    int64_t timestamp, bool pressed) {
    struct zmk_behavior_binding binding = {
        .behavior_dev = behavior_dev,
        .param1 = param,
    };
    struct zmk_behavior_binding_event event = {
        .position = slot->position,
        .timestamp = timestamp,
#if IS_ENABLED(CONFIG_ZMK_SPLIT)
        .source = slot->source,
#endif
    };

    return zmk_behavior_invoke_binding(&binding, event, pressed);
}

static int on_pressed(struct zmk_behavior_binding *binding, struct zmk_behavior_binding_event event) {
    const struct device *dev = zmk_behavior_get_binding(binding->behavior_dev);
    const struct behavior_instant_hold_config *cfg = dev->config;
    struct behavior_instant_hold_data *data = dev->data;
    struct ih_slot *slot = alloc_slot(data);

    if (slot == NULL) {
        LOG_ERR("no free instant-hold slot at position %d", event.position);
        return ZMK_BEHAVIOR_OPAQUE;
    }

    slot->position = event.position;
    slot->hold = binding->param1;
    slot->tap = binding->param2;
    slot->pressed_at = event.timestamp;
#if IS_ENABLED(CONFIG_ZMK_SPLIT)
    slot->source = event.source;
#endif

    /* Press the hold key only for the first physical key that wants it. */
    if (count_hold(data, slot->hold) == 1) {
        LOG_DBG("%d instant hold 0x%04x down", event.position, slot->hold);
        send_key(cfg->hold_behavior_dev, slot->hold, slot, event.timestamp, true);
    }
    return ZMK_BEHAVIOR_OPAQUE;
}

static int on_released(struct zmk_behavior_binding *binding,
                       struct zmk_behavior_binding_event event) {
    const struct device *dev = zmk_behavior_get_binding(binding->behavior_dev);
    const struct behavior_instant_hold_config *cfg = dev->config;
    struct behavior_instant_hold_data *data = dev->data;
    struct ih_slot *slot = find_slot(data, event.position);

    if (slot == NULL) {
        LOG_ERR("instant-hold release with no press at position %d", event.position);
        return ZMK_BEHAVIOR_OPAQUE;
    }

    bool quick = (event.timestamp - slot->pressed_at) < cfg->tapping_term_ms;
    uint32_t hold = slot->hold;
    uint32_t tap = slot->tap;
    struct ih_slot released = *slot;

    slot->position = IH_POSITION_UNUSED;
    int rest = count_hold(data, hold);

    if (quick) {
        /* Lift the hold before the tap, even if another key still wants it,
         * so the tap is not itself a shortcut. Restore the hold afterwards. */
        LOG_DBG("%d instant hold 0x%04x quick tap 0x%04x", event.position, hold, tap);
        send_key(cfg->hold_behavior_dev, hold, &released, event.timestamp, false);
        send_key(cfg->tap_behavior_dev, tap, &released, event.timestamp, true);
        send_key(cfg->tap_behavior_dev, tap, &released, event.timestamp, false);
        if (rest > 0) {
            send_key(cfg->hold_behavior_dev, hold, &released, event.timestamp, true);
        }
    } else if (rest == 0) {
        LOG_DBG("%d instant hold 0x%04x up", event.position, hold);
        send_key(cfg->hold_behavior_dev, hold, &released, event.timestamp, false);
    }
    return ZMK_BEHAVIOR_OPAQUE;
}

#if IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)
static int ih_parameter_metadata(const struct device *dev,
                                 struct behavior_parameter_metadata *param_metadata) {
    const struct behavior_instant_hold_config *cfg = dev->config;
    struct behavior_instant_hold_data *data = dev->data;
    struct behavior_parameter_metadata child_meta;
    int err;

    data->set = (struct behavior_parameter_metadata_set){0};

    err = behavior_get_parameter_metadata(zmk_behavior_get_binding(cfg->hold_behavior_dev),
                                          &child_meta);
    if (err < 0) {
        return err;
    }
    if (child_meta.sets_len > 0) {
        data->set.param1_values = child_meta.sets[0].param1_values;
        data->set.param1_values_len = child_meta.sets[0].param1_values_len;
    }

    err = behavior_get_parameter_metadata(zmk_behavior_get_binding(cfg->tap_behavior_dev),
                                          &child_meta);
    if (err < 0) {
        return err;
    }
    if (child_meta.sets_len > 0) {
        data->set.param2_values = child_meta.sets[0].param1_values;
        data->set.param2_values_len = child_meta.sets[0].param1_values_len;
    }

    param_metadata->sets = &data->set;
    param_metadata->sets_len = 1;
    return 0;
}
#endif

static const struct behavior_driver_api ih_driver_api = {
    .binding_pressed = on_pressed,
    .binding_released = on_released,
#if IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)
    .get_parameter_metadata = ih_parameter_metadata,
#endif
};

#define IH_INST(n)                                                                                 \
    static const struct behavior_instant_hold_config ih_config_##n = {                             \
        .tapping_term_ms = DT_INST_PROP(n, tapping_term_ms),                                       \
        .hold_behavior_dev = DEVICE_DT_NAME(DT_INST_PHANDLE_BY_IDX(n, bindings, 0)),               \
        .tap_behavior_dev = DEVICE_DT_NAME(DT_INST_PHANDLE_BY_IDX(n, bindings, 1)),                \
    };                                                                                             \
    static struct behavior_instant_hold_data ih_data_##n = {};                                     \
    BEHAVIOR_DT_INST_DEFINE(n, ih_init, NULL, &ih_data_##n, &ih_config_##n, POST_KERNEL,           \
                            CONFIG_KERNEL_INIT_PRIORITY_DEFAULT, &ih_driver_api);

DT_INST_FOREACH_STATUS_OKAY(IH_INST)

#endif /* DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT) */
