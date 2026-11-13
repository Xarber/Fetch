// SPDX-License-Identifier: AGPL-3.0-only
import SwiftUI

/// Native navigation, sheets, pickers and press feedback remain system-controlled.
/// Only structural list changes get an app-specific transition, never polling counters.
private struct FetchListMotion<Value: Equatable>: ViewModifier {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    let value: Value
    func body(content: Content) -> some View {
        content.animation(reduceMotion ? nil : .timingCurve(0.23, 1, 0.32, 1, duration: 0.2), value: value)
    }
}
extension View {
    func fetchListMotion<Value: Equatable>(value: Value) -> some View {
        modifier(FetchListMotion(value: value))
    }
}
