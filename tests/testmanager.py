try:
    from unittest.mock import patch, Mock
except ImportError:
    # Py <3.3 compatibility
    from mock import patch, Mock

from trafficdb.manager import create_manager, main

def test_create_manager():
    manager = create_manager()
    assert manager is not None

    import sys
    new_argv = [sys.argv[0], '--help']
    with patch('sys.argv', new_argv), patch('sys.exit', Mock(side_effect=SystemExit)) as exit_mock:
        try:
            # Should raise SystemExit
            manager.run()
        except SystemExit:
            pass
        else:
            assert False

        # Check return value
        exit_mock.assert_called_with(0)

def test_main():
    import sys
    new_argv = [sys.argv[0], '--help']
    with patch('sys.argv', new_argv), patch('sys.exit', Mock(side_effect=SystemExit)) as exit_mock:
        try:
            # Should raise SystemExit
            main()
        except SystemExit:
            pass
        else:
            assert False

        # Check return value
        exit_mock.assert_called_with(0)
