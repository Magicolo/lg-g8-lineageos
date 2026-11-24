/*
 * Copyright 2014 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <cstring>
#include <new>
#include <utility>

#include <gui/BufferItem.h>
#include <gui/BufferItemConsumer.h>
#include <ui/Fence.h>
#include <ui/GraphicBuffer.h>
#include <ui/GraphicBufferMapper.h>
#include <utils/String8.h>

// Legacy Android 12 entry points referenced by the Canadian G8 IMS blobs.
// Keep the symbol wrappers in an IMS-specific library.
android::String8 lg_ims_path_leaf(const android::String8* path)
        asm("_ZNK7android7String811getPathLeafEv");

android::String8 lg_ims_path_leaf(const android::String8* path) {
    const char* separator = std::strrchr(path->c_str(), '/');
    return separator ? android::String8(separator + 1) : android::String8(*path);
}

extern "C" android::status_t lg_ims_mapper_lock(
        android::GraphicBufferMapper* mapper, buffer_handle_t handle, uint32_t usage,
        const android::Rect& bounds, void** address, int32_t* bytesPerPixel, int32_t* bytesPerStride)
        asm("_ZN7android19GraphicBufferMapper4lockEPK13native_handlejRKNS_4RectEPPvPiS9_");

android::status_t lg_ims_mapper_lock(
        android::GraphicBufferMapper* mapper, buffer_handle_t handle, uint32_t usage,
        const android::Rect& bounds, void** address, int32_t* bytesPerPixel, int32_t* bytesPerStride) {
    auto result = mapper->lock(handle, static_cast<int64_t>(usage), bounds);
    if (!result.has_value()) return result.asStatus();
    const auto& buffer = result.value();
    *address = buffer.address;
    if (bytesPerPixel) *bytesPerPixel = buffer.bytesPerPixel;
    if (bytesPerStride) *bytesPerStride = buffer.bytesPerStride;
    return android::OK;
}

extern "C" android::status_t lg_ims_mapper_unlock(
        android::GraphicBufferMapper* mapper, buffer_handle_t handle)
        asm("_ZN7android19GraphicBufferMapper6unlockEPK13native_handle");

android::status_t lg_ims_mapper_unlock(
        android::GraphicBufferMapper* mapper, buffer_handle_t handle) {
    return mapper->unlock(handle, nullptr);
}

// The stock media blob puts a 0x118-byte BufferItem on its stack. Android 17
// adds a picture profile to this class. Keep the old layout in the blob and
// pass a separately constructed Android 17 BufferItem to libgui.
namespace {
struct LegacyBufferItem {
    android::sp<android::GraphicBuffer> graphicBuffer;
    android::sp<android::Fence> fence;
    std::shared_ptr<android::FenceTime> fenceTime{android::FenceTime::NO_FENCE};
    android::Rect crop{android::Rect::INVALID_RECT};
    uint32_t transform{};
    uint32_t scalingMode{};
    int64_t timestamp{};
    bool isAutoTimestamp{};
    android_dataspace dataSpace{HAL_DATASPACE_UNKNOWN};
    android::HdrMetadata hdrMetadata;
    uint64_t frameNumber{};
    int slot{android::BufferItem::INVALID_BUFFER_SLOT};
    bool isDroppable{};
    bool acquireCalled{};
    bool transformToDisplayInverse{};
    android::Region surfaceDamage;
    bool autoRefresh{};
    bool queuedBuffer{true};
    bool isStale{};
    int api{};
};

static_assert(sizeof(LegacyBufferItem) == 0x118);
static_assert(alignof(LegacyBufferItem) == 8);
}  // namespace

extern "C" void lg_ims_bi_construct(LegacyBufferItem* item) {
    new (item) LegacyBufferItem{};
}

extern "C" void lg_ims_bi_destroy(LegacyBufferItem* item) {
    item->~LegacyBufferItem();
}

extern "C" android::status_t lg_ims_bi_acquire(android::BufferItemConsumer* consumer,
                                                      LegacyBufferItem* item,
                                                      nsecs_t presentWhen,
                                                      bool waitForFence) {
    if (item == nullptr) return android::BAD_VALUE;

    android::BufferItem current;
    const auto result = consumer->acquireBuffer(&current, presentWhen, waitForFence);
    if (result != android::OK) return result;

    item->graphicBuffer = std::move(current.mGraphicBuffer);
    item->fence = std::move(current.mFence);
    item->fenceTime = std::move(current.mFenceTime);
    item->crop = current.mCrop;
    item->transform = current.mTransform;
    item->scalingMode = current.mScalingMode;
    item->timestamp = current.mTimestamp;
    item->isAutoTimestamp = current.mIsAutoTimestamp;
    item->dataSpace = current.mDataSpace;
    item->hdrMetadata = std::move(current.mHdrMetadata);
    item->frameNumber = current.mFrameNumber;
    item->slot = current.mSlot;
    item->isDroppable = current.mIsDroppable;
    item->acquireCalled = current.mAcquireCalled;
    item->transformToDisplayInverse = current.mTransformToDisplayInverse;
    item->surfaceDamage = std::move(current.mSurfaceDamage);
    item->autoRefresh = current.mAutoRefresh;
    item->queuedBuffer = current.mQueuedBuffer;
    item->isStale = current.mIsStale;
    item->api = current.mApi;
    return android::OK;
}

extern "C" android::status_t lg_ims_bi_release(
        android::BufferItemConsumer* consumer, const LegacyBufferItem& item,
        const android::sp<android::Fence>& releaseFence) {
    android::BufferItem current;
    current.mGraphicBuffer = item.graphicBuffer;
    current.mSlot = item.slot;
    return consumer->releaseBuffer(current, releaseFence);
}
