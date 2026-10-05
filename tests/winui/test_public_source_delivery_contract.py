"""Public release tag and GPLv3 section 6(d) delivery policy contracts."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "packaging" / "public_source_delivery.py"
POLICY_PATH = ROOT / "packaging" / "PUBLIC_SOURCE_DELIVERY.json"
IDENTITY_PATH = ROOT / "packaging" / "RELEASE_IDENTITY.json"

spec = importlib.util.spec_from_file_location("fly_public_source_delivery", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)


class PublicSourceDeliveryContract(unittest.TestCase):
    def test_current_policy_binds_version_source_assets_and_retention(self):
        policy, identity = module.validate_policy()
        self.assertEqual("6(d)-network-equivalent-access", policy["selected_gplv3_section_6_method"])
        self.assertEqual("v1.0.0.0", policy["release_tag"])
        self.assertEqual(identity["binary_source_revision"], policy["binary_source_revision"])
        self.assertEqual(identity["source_tree_sha"], policy["source_tree_sha"])
        self.assertTrue(policy["designated_public_place"]["binary_and_source_on_same_release_page"])
        self.assertFalse(policy["designated_public_place"]["authentication_required"])
        self.assertFalse(policy["designated_public_place"]["source_additional_charge"])
        self.assertGreaterEqual(
            policy["retention_policy"]["minimum_days_after_last_public_binary_availability"],
            1095,
        )
        self.assertFalse(policy["tag_policy"]["precreate_tag"])
        self.assertTrue(policy["tag_policy"]["create_on_publish"])
        self.assertTrue(policy["tag_policy"]["immutable_releases_required"])

    def test_prepublish_phase_requires_reserved_tag_to_be_absent(self):
        policy, identity = module.validate_policy()
        self.assertIsNone(identity["release_tag"])
        module.validate_git_phase(policy=policy, identity=identity, phase="prepublish")

    def test_policy_rejects_authentication_or_extra_source_charge(self):
        policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        identity = json.loads(IDENTITY_PATH.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(prefix="fly-public-source-policy-") as raw:
            root = Path(raw)
            identity_path = root / "identity.json"
            identity_path.write_text(json.dumps(identity), encoding="utf-8")
            for key in ("authentication_required", "source_additional_charge"):
                broken = deepcopy(policy)
                broken["designated_public_place"][key] = True
                policy_path = root / f"{key}.json"
                policy_path.write_text(json.dumps(broken), encoding="utf-8")
                with self.assertRaises(module.PublicSourcePolicyError):
                    module.validate_policy(
                        policy_path=policy_path,
                        identity_path=identity_path,
                    )

    def test_policy_rejects_short_retention(self):
        policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        identity = json.loads(IDENTITY_PATH.read_text(encoding="utf-8"))
        policy["retention_policy"]["minimum_days_after_last_public_binary_availability"] = 1094
        with tempfile.TemporaryDirectory(prefix="fly-public-source-retention-") as raw:
            root = Path(raw)
            policy_path = root / "policy.json"
            identity_path = root / "identity.json"
            policy_path.write_text(json.dumps(policy), encoding="utf-8")
            identity_path.write_text(json.dumps(identity), encoding="utf-8")
            with self.assertRaises(module.PublicSourcePolicyError):
                module.validate_policy(
                    policy_path=policy_path,
                    identity_path=identity_path,
                )

    def test_required_assets_are_exactly_bound_to_release_identity(self):
        policy, identity = module.validate_policy()
        expected = {
            "flyExplorer-Setup-x64.exe",
            identity["source_bundle"]["file"],
            identity["source_bundle"]["manifest_file"],
            "RELEASE_IDENTITY.json",
            "PAYLOAD_PROVENANCE.json",
            "PAYLOAD_PROVENANCE.md",
        }
        self.assertEqual(expected, set(policy["required_release_assets"]))


if __name__ == "__main__":
    unittest.main()
