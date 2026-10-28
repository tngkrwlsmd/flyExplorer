"""Shared source guard for the one bounded, opt-in L08 movement observer."""


def assert_opt_in_pointer_observer(test, source):
    # Whitespace is incidental; the guard, counter-only callback and cap are not.
    # Remove only this exact allowed observer before rejecting other root moves.
    observer = """
            if(::GetEnvironmentVariableW(
                   L"FLYEXPLORER_COLUMN_RESIZE_DIAGNOSTIC",nullptr,0)>0){
                RootShell().AddHandler(
                    UIElement::PointerMovedEvent(),
                    winrt::box_value(PointerEventHandler{
                        [this](IInspectable const&,
                               Microsoft::UI::Xaml::Input::PointerRoutedEventArgs const&){
                            if(mL08RootPointerMoves<99999)
                                ++mL08RootPointerMoves;
                        }}),
                    true);
            }
        """
    normalized = " ".join(source.split())
    allowed = " ".join(observer.split())
    test.assertEqual(normalized.count(allowed), 1,
                     "L08 observer must remain opt-in, bounded and input-neutral")
    test.assertNotIn("UIElement::PointerMovedEvent()",
                     normalized.replace(allowed, "", 1))
