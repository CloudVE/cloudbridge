"""
Base implementation for data objects exposed through a provider or service
"""
import inspect
import itertools
import logging
import os
import re
import shutil
import time

import six

import cloudbridge.cloud.base.helpers as cb_helpers
from cloudbridge.cloud.interfaces.exceptions \
    import InvalidConfigurationException
from cloudbridge.cloud.interfaces.exceptions import InvalidNameException
from cloudbridge.cloud.interfaces.exceptions import WaitStateException
from cloudbridge.cloud.interfaces.resources import AttachmentInfo
from cloudbridge.cloud.interfaces.resources import Bucket
from cloudbridge.cloud.interfaces.resources import BucketContainer
from cloudbridge.cloud.interfaces.resources import BucketObject
from cloudbridge.cloud.interfaces.resources import CloudResource
from cloudbridge.cloud.interfaces.resources import FloatingIP
from cloudbridge.cloud.interfaces.resources import FloatingIPContainer
from cloudbridge.cloud.interfaces.resources import FloatingIpState
from cloudbridge.cloud.interfaces.resources import GatewayContainer
from cloudbridge.cloud.interfaces.resources import GatewayState
from cloudbridge.cloud.interfaces.resources import Instance
from cloudbridge.cloud.interfaces.resources import InstanceState
from cloudbridge.cloud.interfaces.resources import InternetGateway
from cloudbridge.cloud.interfaces.resources import KeyPair
from cloudbridge.cloud.interfaces.resources import LaunchConfig
from cloudbridge.cloud.interfaces.resources import MachineImage
from cloudbridge.cloud.interfaces.resources import MachineImageState
from cloudbridge.cloud.interfaces.resources import Network
from cloudbridge.cloud.interfaces.resources import NetworkState
from cloudbridge.cloud.interfaces.resources import ObjectLifeCycleMixin
from cloudbridge.cloud.interfaces.resources import PageableObjectMixin
from cloudbridge.cloud.interfaces.resources import PlacementZone
from cloudbridge.cloud.interfaces.resources import Region
from cloudbridge.cloud.interfaces.resources import ResultList
from cloudbridge.cloud.interfaces.resources import Router
from cloudbridge.cloud.interfaces.resources import Snapshot
from cloudbridge.cloud.interfaces.resources import SnapshotState
from cloudbridge.cloud.interfaces.resources import Subnet
from cloudbridge.cloud.interfaces.resources import SubnetState
from cloudbridge.cloud.interfaces.resources import VMFirewall
from cloudbridge.cloud.interfaces.resources import VMFirewallRule
from cloudbridge.cloud.interfaces.resources import VMFirewallRuleContainer
from cloudbridge.cloud.interfaces.resources import VMType
from cloudbridge.cloud.interfaces.resources import Volume
from cloudbridge.cloud.interfaces.resources import VolumeState

log = logging.getLogger(__name__)


class BaseCloudResource(CloudResource):
    """
    Base implementation of a CloudBridge Resource.
    """

    # Regular expression for valid cloudbridge resource names.
    # They, must match the same criteria as GCE labels.
    # as discussed here: https://github.com/CloudVE/cloudbridge/issues/55
    #
    # NOTE: The following regex is based on GCEs internal validation logic,
    # and is significantly complex to allow for international characters.
    CB_NAME_PATTERN = re.compile(six.u(
        r"^[\u0061-\u007A\u00B5\u00DF-\u00F6\u00F8-\u00FF\u0101\u0103\u0105"
        "\u0107\u0109\u010B\u010D\u010F\u0111\u0113\u0115\u0117\u0119\u011B"
        "\u011D\u011F\u0121\u0123\u0125\u0127\u0129\u012B\u012D\u012F\u0131"
        "\u0133\u0135\u0137\u0138\u013A\u013C\u013E\u0140\u0142\u0144\u0146"
        "\u0148\u0149\u014B\u014D\u014F\u0151\u0153\u0155\u0157\u0159\u015B"
        "\u015D\u015F\u0161\u0163\u0165\u0167\u0169\u016B\u016D\u016F\u0171"
        "\u0173\u0175\u0177\u017A\u017C\u017E-\u0180\u0183\u0185\u0188\u018C"
        "\u018D\u0192\u0195\u0199-\u019B\u019E\u01A1\u01A3\u01A5\u01A8\u01AA"
        "\u01AB\u01AD\u01B0\u01B4\u01B6\u01B9\u01BA\u01BD-\u01BF\u01C6\u01C9"
        "\u01CC\u01CE\u01D0\u01D2\u01D4\u01D6\u01D8\u01DA\u01DC\u01DD\u01DF"
        "\u01E1\u01E3\u01E5\u01E7\u01E9\u01EB\u01ED\u01EF\u01F0\u01F3\u01F5"
        "\u01F9\u01FB\u01FD\u01FF\u0201\u0203\u0205\u0207\u0209\u020B\u020D"
        "\u020F\u0211\u0213\u0215\u0217\u0219\u021B\u021D\u021F\u0221\u0223"
        "\u0225\u0227\u0229\u022B\u022D\u022F\u0231\u0233-\u0239\u023C\u023F"
        "\u0240\u0242\u0247\u0249\u024B\u024D\u024F-\u0293\u0295-\u02AF\u0371"
        "\u0373\u0377\u037B-\u037D\u0390\u03AC-\u03CE\u03D0\u03D1\u03D5-"
        "\u03D7\u03D9\u03DB\u03DD\u03DF\u03E1\u03E3\u03E5\u03E7\u03E9\u03EB"
        "\u03ED\u03EF-\u03F3\u03F5\u03F8\u03FB\u03FC\u0430-\u045F\u0461\u0463"
        "\u0465\u0467\u0469\u046B\u046D\u046F\u0471\u0473\u0475\u0477\u0479"
        "\u047B\u047D\u047F\u0481\u048B\u048D\u048F\u0491\u0493\u0495\u0497"
        "\u0499\u049B\u049D\u049F\u04A1\u04A3\u04A5\u04A7\u04A9\u04AB\u04AD"
        "\u04AF\u04B1\u04B3\u04B5\u04B7\u04B9\u04BB\u04BD\u04BF\u04C2\u04C4"
        "\u04C6\u04C8\u04CA\u04CC\u04CE\u04CF\u04D1\u04D3\u04D5\u04D7\u04D9"
        "\u04DB\u04DD\u04DF\u04E1\u04E3\u04E5\u04E7\u04E9\u04EB\u04ED\u04EF"
        "\u04F1\u04F3\u04F5\u04F7\u04F9\u04FB\u04FD\u04FF\u0501\u0503\u0505"
        "\u0507\u0509\u050B\u050D\u050F\u0511\u0513\u0515\u0517\u0519\u051B"
        "\u051D\u051F\u0521\u0523\u0525\u0527\u0561-\u0587\u1D00-\u1D2B"
        "\u1D6B-\u1D77\u1D79-\u1D9A\u1E01\u1E03\u1E05\u1E07\u1E09\u1E0B\u1E0D"
        "\u1E0F\u1E11\u1E13\u1E15\u1E17\u1E19\u1E1B\u1E1D\u1E1F\u1E21\u1E23"
        "\u1E25\u1E27\u1E29\u1E2B\u1E2D\u1E2F\u1E31\u1E33\u1E35\u1E37\u1E39"
        "\u1E3B\u1E3D\u1E3F\u1E41\u1E43\u1E45\u1E47\u1E49\u1E4B\u1E4D\u1E4F"
        "\u1E51\u1E53\u1E55\u1E57\u1E59\u1E5B\u1E5D\u1E5F\u1E61\u1E63\u1E65"
        "\u1E67\u1E69\u1E6B\u1E6D\u1E6F\u1E71\u1E73\u1E75\u1E77\u1E79\u1E7B"
        "\u1E7D\u1E7F\u1E81\u1E83\u1E85\u1E87\u1E89\u1E8B\u1E8D\u1E8F\u1E91"
        "\u1E93\u1E95-\u1E9D\u1E9F\u1EA1\u1EA3\u1EA5\u1EA7\u1EA9\u1EAB\u1EAD"
        "\u1EAF\u1EB1\u1EB3\u1EB5\u1EB7\u1EB9\u1EBB\u1EBD\u1EBF\u1EC1\u1EC3"
        "\u1EC5\u1EC7\u1EC9\u1ECB\u1ECD\u1ECF\u1ED1\u1ED3\u1ED5\u1ED7\u1ED9"
        "\u1EDB\u1EDD\u1EDF\u1EE1\u1EE3\u1EE5\u1EE7\u1EE9\u1EEB\u1EED\u1EEF"
        "\u1EF1\u1EF3\u1EF5\u1EF7\u1EF9\u1EFB\u1EFD\u1EFF-\u1F07\u1F10-\u1F15"
        "\u1F20-\u1F27\u1F30-\u1F37\u1F40-\u1F45\u1F50-\u1F57\u1F60-\u1F67"
        "\u1F70-\u1F7D\u1F80-\u1F87\u1F90-\u1F97\u1FA0-\u1FA7\u1FB0-\u1FB4"
        "\u1FB6\u1FB7\u1FBE\u1FC2-\u1FC4\u1FC6\u1FC7\u1FD0-\u1FD3\u1FD6\u1FD7"
        "\u1FE0-\u1FE7\u1FF2-\u1FF4\u1FF6\u1FF7\u210A\u210E\u210F\u2113\u212F"
        "\u2134\u2139\u213C\u213D\u2146-\u2149\u214E\u2184\u2C30-\u2C5E\u2C61"
        "\u2C65\u2C66\u2C68\u2C6A\u2C6C\u2C71\u2C73\u2C74\u2C76-\u2C7B\u2C81"
        "\u2C83\u2C85\u2C87\u2C89\u2C8B\u2C8D\u2C8F\u2C91\u2C93\u2C95\u2C97"
        "\u2C99\u2C9B\u2C9D\u2C9F\u2CA1\u2CA3\u2CA5\u2CA7\u2CA9\u2CAB\u2CAD"
        "\u2CAF\u2CB1\u2CB3\u2CB5\u2CB7\u2CB9\u2CBB\u2CBD\u2CBF\u2CC1\u2CC3"
        "\u2CC5\u2CC7\u2CC9\u2CCB\u2CCD\u2CCF\u2CD1\u2CD3\u2CD5\u2CD7\u2CD9"
        "\u2CDB\u2CDD\u2CDF\u2CE1\u2CE3\u2CE4\u2CEC\u2CEE\u2CF3\u2D00-\u2D25"
        "\u2D27\u2D2D\uA641\uA643\uA645\uA647\uA649\uA64B\uA64D\uA64F\uA651"
        "\uA653\uA655\uA657\uA659\uA65B\uA65D\uA65F\uA661\uA663\uA665\uA667"
        "\uA669\uA66B\uA66D\uA681\uA683\uA685\uA687\uA689\uA68B\uA68D\uA68F"
        "\uA691\uA693\uA695\uA697\uA723\uA725\uA727\uA729\uA72B\uA72D\uA72F-"
        "\uA731\uA733\uA735\uA737\uA739\uA73B\uA73D\uA73F\uA741\uA743\uA745"
        "\uA747\uA749\uA74B\uA74D\uA74F\uA751\uA753\uA755\uA757\uA759\uA75B"
        "\uA75D\uA75F\uA761\uA763\uA765\uA767\uA769\uA76B\uA76D\uA76F\uA771-"
        "\uA778\uA77A\uA77C\uA77F\uA781\uA783\uA785\uA787\uA78C\uA78E\uA791"
        "\uA793\uA7A1\uA7A3\uA7A5\uA7A7\uA7A9\uA7FA\uFB00-\uFB06\uFB13-\uFB17"
        "\uFF41-\uFF5A\u00AA\u00BA\u01BB\u01C0-\u01C3\u0294\u05D0-\u05EA"
        "\u05F0-\u05F2\u0620-\u063F\u0641-\u064A\u066E\u066F\u0671-\u06D3"
        "\u06D5\u06EE\u06EF\u06FA-\u06FC\u06FF\u0710\u0712-\u072F\u074D-"
        "\u07A5\u07B1\u07CA-\u07EA\u0800-\u0815\u0840-\u0858\u08A0\u08A2-"
        "\u08AC\u0904-\u0939\u093D\u0950\u0958-\u0961\u0972-\u0977\u0979-"
        "\u097F\u0985-\u098C\u098F\u0990\u0993-\u09A8\u09AA-\u09B0\u09B2"
        "\u09B6-\u09B9\u09BD\u09CE\u09DC\u09DD\u09DF-\u09E1\u09F0\u09F1"
        "\u0A05-\u0A0A\u0A0F\u0A10\u0A13-\u0A28\u0A2A-\u0A30\u0A32\u0A33"
        "\u0A35\u0A36\u0A38\u0A39\u0A59-\u0A5C\u0A5E\u0A72-\u0A74\u0A85-"
        "\u0A8D\u0A8F-\u0A91\u0A93-\u0AA8\u0AAA-\u0AB0\u0AB2\u0AB3\u0AB5-"
        "\u0AB9\u0ABD\u0AD0\u0AE0\u0AE1\u0B05-\u0B0C\u0B0F\u0B10\u0B13-"
        "\u0B28\u0B2A-\u0B30\u0B32\u0B33\u0B35-\u0B39\u0B3D\u0B5C\u0B5D"
        "\u0B5F-\u0B61\u0B71\u0B83\u0B85-\u0B8A\u0B8E-\u0B90\u0B92-\u0B95"
        "\u0B99\u0B9A\u0B9C\u0B9E\u0B9F\u0BA3\u0BA4\u0BA8-\u0BAA\u0BAE-"
        "\u0BB9\u0BD0\u0C05-\u0C0C\u0C0E-\u0C10\u0C12-\u0C28\u0C2A-\u0C33"
        "\u0C35-\u0C39\u0C3D\u0C58\u0C59\u0C60\u0C61\u0C85-\u0C8C\u0C8E-"
        "\u0C90\u0C92-\u0CA8\u0CAA-\u0CB3\u0CB5-\u0CB9\u0CBD\u0CDE\u0CE0"
        "\u0CE1\u0CF1\u0CF2\u0D05-\u0D0C\u0D0E-\u0D10\u0D12-\u0D3A\u0D3D"
        "\u0D4E\u0D60\u0D61\u0D7A-\u0D7F\u0D85-\u0D96\u0D9A-\u0DB1\u0DB3-"
        "\u0DBB\u0DBD\u0DC0-\u0DC6\u0E01-\u0E30\u0E32\u0E33\u0E40-\u0E45"
        "\u0E81\u0E82\u0E84\u0E87\u0E88\u0E8A\u0E8D\u0E94-\u0E97\u0E99-"
        "\u0E9F\u0EA1-\u0EA3\u0EA5\u0EA7\u0EAA\u0EAB\u0EAD-\u0EB0\u0EB2"
        "\u0EB3\u0EBD\u0EC0-\u0EC4\u0EDC-\u0EDF\u0F00\u0F40-\u0F47\u0F49-"
        "\u0F6C\u0F88-\u0F8C\u1000-\u102A\u103F\u1050-\u1055\u105A-\u105D"
        "\u1061\u1065\u1066\u106E-\u1070\u1075-\u1081\u108E\u10D0-\u10FA"
        "\u10FD-\u1248\u124A-\u124D\u1250-\u1256\u1258\u125A-\u125D\u1260-"
        "\u1288\u128A-\u128D\u1290-\u12B0\u12B2-\u12B5\u12B8-\u12BE\u12C0"
        "\u12C2-\u12C5\u12C8-\u12D6\u12D8-\u1310\u1312-\u1315\u1318-\u135A"
        "\u1380-\u138F\u13A0-\u13F4\u1401-\u166C\u166F-\u167F\u1681-\u169A"
        "\u16A0-\u16EA\u1700-\u170C\u170E-\u1711\u1720-\u1731\u1740-\u1751"
        "\u1760-\u176C\u176E-\u1770\u1780-\u17B3\u17DC\u1820-\u1842\u1844-"
        "\u1877\u1880-\u18A8\u18AA\u18B0-\u18F5\u1900-\u191C\u1950-\u196D"
        "\u1970-\u1974\u1980-\u19AB\u19C1-\u19C7\u1A00-\u1A16\u1A20-\u1A54"
        "\u1B05-\u1B33\u1B45-\u1B4B\u1B83-\u1BA0\u1BAE\u1BAF\u1BBA-\u1BE5"
        "\u1C00-\u1C23\u1C4D-\u1C4F\u1C5A-\u1C77\u1CE9-\u1CEC\u1CEE-\u1CF1"
        "\u1CF5\u1CF6\u2135-\u2138\u2D30-\u2D67\u2D80-\u2D96\u2DA0-\u2DA6"
        "\u2DA8-\u2DAE\u2DB0-\u2DB6\u2DB8-\u2DBE\u2DC0-\u2DC6\u2DC8-\u2DCE"
        "\u2DD0-\u2DD6\u2DD8-\u2DDE\u3006\u303C\u3041-\u3096\u309F\u30A1-"
        "\u30FA\u30FF\u3105-\u312D\u3131-\u318E\u31A0-\u31BA\u31F0-\u31FF"
        "\u3400-\u4DB5\u4E00-\u9FCC\uA000-\uA014\uA016-\uA48C\uA4D0-\uA4F7"
        "\uA500-\uA60B\uA610-\uA61F\uA62A\uA62B\uA66E\uA6A0-\uA6E5\uA7FB-"
        "\uA801\uA803-\uA805\uA807-\uA80A\uA80C-\uA822\uA840-\uA873\uA882-"
        "\uA8B3\uA8F2-\uA8F7\uA8FB\uA90A-\uA925\uA930-\uA946\uA960-\uA97C"
        "\uA984-\uA9B2\uAA00-\uAA28\uAA40-\uAA42\uAA44-\uAA4B\uAA60-\uAA6F"
        "\uAA71-\uAA76\uAA7A\uAA80-\uAAAF\uAAB1\uAAB5\uAAB6\uAAB9-\uAABD"
        "\uAAC0\uAAC2\uAADB\uAADC\uAAE0-\uAAEA\uAAF2\uAB01-\uAB06\uAB09-"
        "\uAB0E\uAB11-\uAB16\uAB20-\uAB26\uAB28-\uAB2E\uABC0-\uABE2\uAC00-"
        "\uD7A3\uD7B0-\uD7C6\uD7CB-\uD7FB\uF900-\uFA6D\uFA70-\uFAD9\uFB1D"
        "\uFB1F-\uFB28\uFB2A-\uFB36\uFB38-\uFB3C\uFB3E\uFB40\uFB41\uFB43"
        "\uFB44\uFB46-\uFBB1\uFBD3-\uFD3D\uFD50-\uFD8F\uFD92-\uFDC7\uFDF0-"
        "\uFDFB\uFE70-\uFE74\uFE76-\uFEFC\uFF66-\uFF6F\uFF71-\uFF9D\uFFA0-"
        "\uFFBE\uFFC2-\uFFC7\uFFCA-\uFFCF\uFFD2-\uFFD7\uFFDA-\uFFDC\u0030-"
        "\u0039\u00B2\u00B3\u00B9\u00BC-\u00BE\u0660-\u0669\u06F0-\u06F9"
        "\u07C0-\u07C9\u0966-\u096F\u09E6-\u09EF\u09F4-\u09F9\u0A66-\u0A6F"
        "\u0AE6-\u0AEF\u0B66-\u0B6F\u0B72-\u0B77\u0BE6-\u0BF2\u0C66-\u0C6F"
        "\u0C78-\u0C7E\u0CE6-\u0CEF\u0D66-\u0D75\u0E50-\u0E59\u0ED0-\u0ED9"
        "\u0F20-\u0F33\u1040-\u1049\u1090-\u1099\u1369-\u137C\u16EE-\u16F0"
        "\u17E0-\u17E9\u17F0-\u17F9\u1810-\u1819\u1946-\u194F\u19D0-\u19DA"
        "\u1A80-\u1A89\u1A90-\u1A99\u1B50-\u1B59\u1BB0-\u1BB9\u1C40-\u1C49"
        "\u1C50-\u1C59\u2070\u2074-\u2079\u2080-\u2089\u2150-\u2182\u2185-"
        "\u2189\u2460-\u249B\u24EA-\u24FF\u2776-\u2793\u2CFD\u3007\u3021-"
        "\u3029\u3038-\u303A\u3192-\u3195\u3220-\u3229\u3248-\u324F\u3251-"
        "\u325F\u3280-\u3289\u32B1-\u32BF\uA620-\uA629\uA6E6-\uA6EF\uA830-"
        "\uA835\uA8D0-\uA8D9\uA900-\uA909\uA9D0-\uA9D9\uAA50-\uAA59\uABF0-"
        "\uABF9\uFF10-\uFF19_-]{0,63}$"), re.UNICODE)

    def __init__(self, provider):
        self.__provider = provider

    @staticmethod
    def is_valid_resource_name(name):
        return True if BaseCloudResource.CB_NAME_PATTERN.match(name) else False

    @staticmethod
    def assert_valid_resource_name(name):
        if not BaseCloudResource.is_valid_resource_name(name):
            log.debug("InvalidNameException raised on %s", name)
            raise InvalidNameException(
                u"Invalid name: %s. Name must be at most 63 characters "
                "long and consist of lowercase letters, numbers, "
                "underscores, dashes or international characters" % name)

    @property
    def _provider(self):
        return self.__provider

    def to_json(self):
        # Get all attributes but filter methods and private/magic ones
        attr = inspect.getmembers(self, lambda a: not(inspect.isroutine(a)))
        js = {k: v for(k, v) in attr if not k.startswith('_')}
        return js


class BaseObjectLifeCycleMixin(ObjectLifeCycleMixin):
    """
    A base implementation of an ObjectLifeCycleMixin.
    This base implementation has an implementation of wait_for
    which refreshes the object's state till the desired ready states
    are reached. Subclasses must still implement the wait_till_ready
    method, since the desired ready states are object specific.
    """

    def wait_for(self, target_states, terminal_states=None, timeout=None,
                 interval=None):
        if timeout is None:
            timeout = self._provider.config.default_wait_timeout
        if interval is None:
            interval = self._provider.config.default_wait_interval

        assert timeout >= 0
        assert interval >= 0
        assert timeout >= interval

        end_time = time.time() + timeout

        while self.state not in target_states:
            if self.state in (terminal_states or []):
                raise WaitStateException(
                    "Object: {0} is in state: {1} which is a terminal state"
                    " and cannot be waited on.".format(self, self.state))
            else:
                log.debug(
                    "Object %s is in state: %s. Waiting another %s"
                    " seconds to reach target state(s): %s...",
                    self,
                    self.state,
                    int(end_time - time.time()),
                    target_states)
                time.sleep(interval)
                if time.time() > end_time:
                    raise WaitStateException(
                        "Waited too long for object: {0} to become ready. It's"
                        " still in state: {1}".format(self, self.state))
            self.refresh()
        log.debug("Object: %s successfully reached target state: %s",
                  self, self.state)
        return True


class BaseResultList(ResultList):

    def __init__(
            self, is_truncated, marker, supports_total, total=None, data=None):
        # call list constructor
        super(BaseResultList, self).__init__(data or [])
        self._marker = marker
        self._is_truncated = is_truncated
        self._supports_total = True if supports_total else False
        self._total = total

    @property
    def marker(self):
        return self._marker

    @property
    def is_truncated(self):
        return self._is_truncated

    @property
    def supports_total(self):
        return self._supports_total

    @property
    def total_results(self):
        return self._total


class ServerPagedResultList(BaseResultList):
    """
    This is a convenience class that extends the :class:`BaseResultList` class
    and provides a server side implementation of paging. It is meant for use by
    provider developers and is not meant for direct use by end-users.
    This class can be used to wrap a partial result list when an operation
    supports server side paging.
    """

    @property
    def supports_server_paging(self):
        return True

    @property
    def data(self):
        raise NotImplementedError(
            "ServerPagedResultLists do not support the data property")


class ClientPagedResultList(BaseResultList):
    """
    This is a convenience class that extends the :class:`BaseResultList` class
    and provides a client side implementation of paging. It is meant for use by
    provider developers and is not meant for direct use by end-users.
    This class can be used to wrap a full result list when an operation does
    not support server side paging. This class will then provide a paged view
    of the full result set entirely on the client side.
    """

    def __init__(self, provider, objects, limit=None, marker=None):
        self._objects = objects
        limit = limit or provider.config.default_result_limit
        total_size = len(objects)
        if marker:
            from_marker = itertools.dropwhile(
                lambda obj: not obj.id == marker, objects)
            # skip one past the marker
            next(from_marker, None)
            objects = list(from_marker)
        is_truncated = len(objects) > limit
        results = list(itertools.islice(objects, limit))
        super(ClientPagedResultList, self).__init__(
            is_truncated,
            results[-1].id if is_truncated else None,
            True, total=total_size,
            data=results)

    @property
    def supports_server_paging(self):
        return False

    @property
    def data(self):
        return self._objects


class BasePageableObjectMixin(PageableObjectMixin):
    """
    A mixin to provide iteration capability for a class
    that support a list(limit, marker) method.
    """

    def __iter__(self):
        result_list = self.list()
        if result_list.supports_server_paging:
            for result in result_list:
                yield result
            while result_list.is_truncated:
                result_list = self.list(marker=result_list.marker)
                for result in result_list:
                    yield result
        else:
            for result in result_list.data:
                yield result


class BaseVMType(BaseCloudResource, VMType):

    def __init__(self, provider):
        super(BaseVMType, self).__init__(provider)

    def __eq__(self, other):
        return (isinstance(other, VMType) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)

    @property
    def size_total_disk(self):
        return self.size_root_disk + self.size_ephemeral_disks

    def __repr__(self):
        return "<CB-{0}: {1} ({2})>".format(self.__class__.__name__,
                                            self.name, self.id)


class BaseInstance(BaseCloudResource, BaseObjectLifeCycleMixin, Instance):

    def __init__(self, provider):
        super(BaseInstance, self).__init__(provider)

    def __eq__(self, other):
        return (isinstance(other, Instance) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id and
                # check from most to least likely mutables
                self.state == other.state and
                self.name == other.name and
                self.vm_firewalls == other.vm_firewalls and
                self.public_ips == other.public_ips and
                self.private_ips == other.private_ips and
                self.image_id == other.image_id)

    def wait_till_ready(self, timeout=None, interval=None):
        self.wait_for(
            [InstanceState.RUNNING],
            terminal_states=[InstanceState.DELETED, InstanceState.ERROR],
            timeout=timeout,
            interval=interval)

    def __repr__(self):
        return "<CB-{0}: {1} ({2})>".format(self.__class__.__name__,
                                            self.name, self.id)


class BaseLaunchConfig(LaunchConfig):

    def __init__(self, provider):
        self.provider = provider
        self.block_devices = []

    class BlockDeviceMapping(object):
        """
        Represents a block device mapping
        """

        def __init__(self, is_volume=False, source=None, is_root=None,
                     size=None, delete_on_terminate=None):
            self.is_volume = is_volume
            self.source = source
            self.is_root = is_root
            self.size = size
            self.delete_on_terminate = delete_on_terminate

    def add_ephemeral_device(self):
        block_device = BaseLaunchConfig.BlockDeviceMapping()
        self.block_devices.append(block_device)

    def add_volume_device(self, source=None, is_root=None, size=None,
                          delete_on_terminate=None):
        block_device = self._validate_volume_device(
            source=source, is_root=is_root, size=size,
            delete_on_terminate=delete_on_terminate)
        log.debug("Appending %s to the block_devices list",
                  block_device)
        self.block_devices.append(block_device)

    def _validate_volume_device(self, source=None, is_root=None,
                                size=None, delete_on_terminate=None):
        """
        Validates a volume based device and throws an
        InvalidConfigurationException if the configuration is incorrect.
        """
        if source is None and not size:
            log.exception("InvalidConfigurationException raised: "
                          "no size argument specified.")
            raise InvalidConfigurationException(
                "A size must be specified for a blank new volume.")

        if source and \
                not isinstance(source, (Snapshot, Volume, MachineImage)):
            log.exception("InvalidConfigurationException raised: "
                          "source argument not specified correctly.")
            raise InvalidConfigurationException(
                "Source must be a Snapshot, Volume, MachineImage, or None.")
        if size:
            if not isinstance(size, six.integer_types) or not size > 0:
                log.exception("InvalidConfigurationException raised: "
                              "size argument must be an integer greater than "
                              "0. Got type %s and value %s.", type(size), size)
                raise InvalidConfigurationException(
                    "The size must be None or an integer greater than 0.")

        if is_root:
            for bd in self.block_devices:
                if bd.is_root:
                    log.exception("InvalidConfigurationException raised: "
                                  "%s has already been marked as the root "
                                  "block device.", bd)
                    raise InvalidConfigurationException(
                        "An existing block device: {0} has already been"
                        " marked as root. There can only be one root device.")

        return BaseLaunchConfig.BlockDeviceMapping(
            is_volume=True, source=source, is_root=is_root, size=size,
            delete_on_terminate=delete_on_terminate)


class BaseMachineImage(
        BaseCloudResource, BaseObjectLifeCycleMixin, MachineImage):

    def __init__(self, provider):
        super(BaseMachineImage, self).__init__(provider)

    def __eq__(self, other):
        return (isinstance(other, MachineImage) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id and
                # check from most to least likely mutables
                self.state == other.state and
                self.name == other.name and
                self.description == other.description)

    def wait_till_ready(self, timeout=None, interval=None):
        self.wait_for(
            [MachineImageState.AVAILABLE],
            terminal_states=[MachineImageState.ERROR],
            timeout=timeout,
            interval=interval)

    def __repr__(self):
        return "<CB-{0}: {1} ({2})>".format(self.__class__.__name__,
                                            self.name, self.id)


class BaseAttachmentInfo(AttachmentInfo):

    def __init__(self, volume, instance_id, device):
        self._volume = volume
        self._instance_id = instance_id
        self._device = device

    @property
    def volume(self):
        return self._volume

    @property
    def instance_id(self):
        return self._instance_id

    @property
    def device(self):
        return self._device


class BaseVolume(BaseCloudResource, BaseObjectLifeCycleMixin, Volume):

    def __init__(self, provider):
        super(BaseVolume, self).__init__(provider)

    def __eq__(self, other):
        return (isinstance(other, Volume) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id and
                # check from most to least likely mutables
                self.state == other.state and
                self.name == other.name)

    def wait_till_ready(self, timeout=None, interval=None):
        self.wait_for(
            [VolumeState.AVAILABLE],
            terminal_states=[VolumeState.ERROR, VolumeState.DELETED],
            timeout=timeout,
            interval=interval)

    def __repr__(self):
        return "<CB-{0}: {1} ({2})>".format(self.__class__.__name__,
                                            self.name, self.id)


class BaseSnapshot(BaseCloudResource, BaseObjectLifeCycleMixin, Snapshot):

    def __init__(self, provider):
        super(BaseSnapshot, self).__init__(provider)

    def __eq__(self, other):
        return (isinstance(other, Snapshot) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id and
                # check from most to least likely mutables
                self.state == other.state and
                self.name == other.name)

    def wait_till_ready(self, timeout=None, interval=None):
        self.wait_for(
            [SnapshotState.AVAILABLE],
            terminal_states=[SnapshotState.ERROR],
            timeout=timeout,
            interval=interval)

    def __repr__(self):
        return "<CB-{0}: {1} ({2})>".format(self.__class__.__name__,
                                            self.name, self.id)


class BaseKeyPair(BaseCloudResource, KeyPair):

    def __init__(self, provider, key_pair):
        super(BaseKeyPair, self).__init__(provider)
        self._key_pair = key_pair
        self._private_material = None

    def __eq__(self, other):
        return (isinstance(other, KeyPair) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.name == other.name)

    @property
    def id(self):
        """
        Return the id of this key pair.
        """
        return self._key_pair.name

    @property
    def name(self):
        """
        Return the name of this key pair.
        """
        return self._key_pair.name

    @property
    def material(self):
        return self._private_material

    @material.setter
    # pylint:disable=arguments-differ
    def material(self, value):
        self._private_material = value

    def delete(self):
        """
        Delete this KeyPair.

        :rtype: bool
        :return: True if successful, otherwise False.
        """
        # This implementation assumes the `delete` method exists across
        #  multiple providers.
        self._key_pair.delete()

    def __repr__(self):
        return "<CBKeyPair: {0}>".format(self.name)


class BaseVMFirewall(BaseCloudResource, VMFirewall):

    def __init__(self, provider, vm_firewall):
        super(BaseVMFirewall, self).__init__(provider)
        self._vm_firewall = vm_firewall

    def __eq__(self, other):
        """
        Check if all the defined rules match across both VM firewalls.
        """
        return (isinstance(other, VMFirewall) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                set(self.rules) == set(other.rules))

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def id(self):
        """
        Get the ID of this VM firewall.

        :rtype: str
        :return: VM firewall ID
        """
        return self._vm_firewall.id

    @property
    def name(self):
        """
        Return the name of this VM firewall.
        """
        return self._vm_firewall.name

    @property
    def description(self):
        """
        Return the description of this VM firewall.
        """
        return self._vm_firewall.description

    def delete(self):
        """
        Delete this VM firewall.
        """
        return self._vm_firewall.delete()

    def __repr__(self):
        return "<CB-{0}: {1} ({2})>".format(self.__class__.__name__,
                                            self.id, self.name)


class BaseVMFirewallRuleContainer(BasePageableObjectMixin,
                                  VMFirewallRuleContainer):

    def __init__(self, provider, firewall):
        self.__provider = provider
        self.firewall = firewall

    @property
    def _provider(self):
        return self.__provider

    def get(self, rule_id):
        matches = [rule for rule in self if rule.id == rule_id]
        if matches:
            return matches[0]
        else:
            return None

    def find(self, **kwargs):
        obj_list = self
        filters = ['name', 'direction', 'protocol', 'from_port', 'to_port',
                   'cidr', 'src_dest_fw', 'src_dest_fw_id']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))

    def delete(self, rule_id):
        rule = self.get(rule_id)
        if rule:
            rule.delete()


class BaseVMFirewallRule(BaseCloudResource, VMFirewallRule):

    def __init__(self, parent_fw, rule):
        # pylint:disable=protected-access
        super(BaseVMFirewallRule, self).__init__(
            parent_fw._provider)
        self.firewall = parent_fw
        self._rule = rule

        # Cache name
        self._name = "{0}-{1}-{2}-{3}-{4}-{5}".format(
            self.direction, self.protocol, self.from_port, self.to_port,
            self.cidr, self.src_dest_fw_id).lower()

    @property
    def name(self):
        return self._name

    def __repr__(self):
        return ("<{0}: id: {1}; direction: {2}; protocol: {3};  from: {4};"
                " to: {5}; cidr: {6}, src_dest_fw: {7}>"
                .format(self.__class__.__name__, self.id, self.direction,
                        self.protocol, self.from_port, self.to_port, self.cidr,
                        self.src_dest_fw_id))

    def __eq__(self, other):
        return (isinstance(other, VMFirewallRule) and
                self.direction == other.direction and
                self.protocol == other.protocol and
                self.from_port == other.from_port and
                self.to_port == other.to_port and
                self.cidr == other.cidr and
                self.src_dest_fw_id == other.src_dest_fw_id)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        """
        Return a hash-based interpretation of all of the object's field values.

        This is requeried for operations on hashed collections including
        ``set``, ``frozenset``, and ``dict``.
        """
        return hash("{0}{1}{2}{3}{4}{5}".format(
            self.direction, self.protocol, self.from_port, self.to_port,
            self.cidr, self.src_dest_fw_id))

    def to_json(self):
        attr = inspect.getmembers(self, lambda a: not (inspect.isroutine(a)))
        js = {k: v for (k, v) in attr if not k.startswith('_')}
        js['src_dest_fw'] = self.src_dest_fw_id
        js['firewall'] = self.firewall.id
        return js


class BasePlacementZone(BaseCloudResource, PlacementZone):

    def __init__(self, provider):
        super(BasePlacementZone, self).__init__(provider)

    def __repr__(self):
        return "<CB-{0}: {1}>".format(self.__class__.__name__,
                                      self.id)

    def __eq__(self, other):
        return (isinstance(other, PlacementZone) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)


class BaseRegion(BaseCloudResource, Region):

    def __init__(self, provider):
        super(BaseRegion, self).__init__(provider)

    def __repr__(self):
        return "<CB-{0}: {1}>".format(self.__class__.__name__,
                                      self.id)

    def __eq__(self, other):
        return (isinstance(other, Region) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)

    def to_json(self):
        attr = inspect.getmembers(self, lambda a: not(inspect.isroutine(a)))
        js = {k: v for(k, v) in attr if not k.startswith('_')}
        js['zones'] = [z.name for z in self.zones]
        return js


class BaseBucketObject(BaseCloudResource, BucketObject):

    # Regular expression for valid bucket keys.
    # They, must match the following criteria: http://docs.aws.amazon.com/"
    # AmazonS3/latest/dev/UsingMetadata.html#object-key-guidelines
    #
    # Note: The following regex is based on: https://stackoverflow.com/question
    # s/537772/what-is-the-most-correct-regular-expression-for-a-unix-file-path
    CB_NAME_PATTERN = re.compile(r"[^\0]+")

    def __init__(self, provider):
        super(BaseBucketObject, self).__init__(provider)

    @staticmethod
    def is_valid_resource_name(name):
        return True if BaseBucketObject.CB_NAME_PATTERN.match(name) else False

    @staticmethod
    def assert_valid_resource_name(name):
        if not BaseBucketObject.is_valid_resource_name(name):
            log.debug("InvalidNameException raised on %s", name, exc_info=True)
            raise InvalidNameException(
                u"Invalid object name: %s. Name must match criteria defined "
                "in: http://docs.aws.amazon.com/AmazonS3/latest/dev/UsingMeta"
                "data.html#object-key-guidelines" % name)

    def save_content(self, target_stream):
        shutil.copyfileobj(self.iter_content(), target_stream)

    def __eq__(self, other):
        return (isinstance(other, BucketObject) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id and
                # check from most to least likely mutables
                self.name == other.name)

    def __repr__(self):
        return "<CB-{0}: {1}>".format(self.__class__.__name__,
                                      self.name)


class BaseBucket(BaseCloudResource, Bucket):

    # Regular expression for valid bucket names.
    # They, must match the following criteria: http://docs.aws.amazon.com/aws
    # cloudtrail/latest/userguide/cloudtrail-s3-bucket-naming-requirements.html
    #
    # NOTE: The following regex is based on: https://stackoverflow.com/questio
    # ns/2063213/regular-expression-for-validating-dns-label-host-name
    CB_NAME_PATTERN = re.compile(r"^(?![0-9]+$)(?!-)[a-z0-9-]{3,63}(?<!-)$")

    def __init__(self, provider):
        super(BaseBucket, self).__init__(provider)

    @staticmethod
    def is_valid_resource_name(name):
        return True if BaseBucket.CB_NAME_PATTERN.match(name) else False

    @staticmethod
    def assert_valid_resource_name(name):
        if not BaseBucket.is_valid_resource_name(name):
            log.debug("Invalid resource name %s", name, exc_info=True)
            raise InvalidNameException(
                u"Invalid bucket name: %s. Name must match criteria defined "
                "in: http://docs.aws.amazon.com/awscloudtrail/latest/userguide"
                "/cloudtrail-s3-bucket-naming-requirements.html" % name)

    def __eq__(self, other):
        return (isinstance(other, Bucket) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id and
                # check from most to least likely mutables
                self.name == other.name)

    def __repr__(self):
        return "<CB-{0}: {1}>".format(self.__class__.__name__,
                                      self.name)


class BaseBucketContainer(BasePageableObjectMixin, BucketContainer):

    def __init__(self, provider, bucket):
        self.__provider = provider
        self.bucket = bucket

    @property
    def _provider(self):
        return self.__provider


class BaseGatewayContainer(GatewayContainer, BasePageableObjectMixin):

    def __init__(self, provider, network):
        self._network = network
        self._provider = provider


class BaseNetwork(BaseCloudResource, BaseObjectLifeCycleMixin, Network):

    CB_DEFAULT_NETWORK_NAME = os.environ.get('CB_DEFAULT_NETWORK_NAME',
                                             'cloudbridge-net')

    def __init__(self, provider):
        super(BaseNetwork, self).__init__(provider)

    def __repr__(self):
        return "<CB-{0}: {1} ({2})>".format(self.__class__.__name__,
                                            self.id, self.name)

    def wait_till_ready(self, timeout=None, interval=None):
        self.wait_for(
            [NetworkState.AVAILABLE],
            terminal_states=[NetworkState.ERROR],
            timeout=timeout,
            interval=interval)

    def create_subnet(self, name, cidr_block, zone=None):
        return self._provider.networking.subnets.create(
            name=name, network=self, cidr_block=cidr_block, zone=zone)

    def __eq__(self, other):
        return (isinstance(other, Network) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)


class BaseSubnet(BaseCloudResource, BaseObjectLifeCycleMixin, Subnet):

    CB_DEFAULT_SUBNET_NAME = os.environ.get('CB_DEFAULT_SUBNET_NAME',
                                            'cloudbridge-subnet')

    def __init__(self, provider):
        super(BaseSubnet, self).__init__(provider)

    def __repr__(self):
        return "<CB-{0}: {1} ({2})>".format(self.__class__.__name__,
                                            self.id, self.name)

    def __eq__(self, other):
        return (isinstance(other, Subnet) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)

    def wait_till_ready(self, timeout=None, interval=None):
        self.wait_for(
            [SubnetState.AVAILABLE],
            terminal_states=[SubnetState.ERROR],
            timeout=timeout,
            interval=interval)


class BaseFloatingIPContainer(FloatingIPContainer, BasePageableObjectMixin):

    def __init__(self, provider, gateway):
        self.__provider = provider
        self.gateway = gateway

    @property
    def _provider(self):
        return self.__provider

    def find(self, **kwargs):
        obj_list = self
        filters = ['name', 'public_ip']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))

    def delete(self, fip_id):
        floating_ip = self.get(fip_id)
        if floating_ip:
            floating_ip.delete()


class BaseFloatingIP(BaseCloudResource, BaseObjectLifeCycleMixin, FloatingIP):

    def __init__(self, provider):
        super(BaseFloatingIP, self).__init__(provider)

    @property
    def name(self):
        # VM firewall rules don't support names, so pass
        return self.public_ip

    @property
    def state(self):
        return (FloatingIpState.IN_USE if self.in_use
                else FloatingIpState.AVAILABLE)

    def wait_till_ready(self, timeout=None, interval=None):
        self.wait_for(
            [FloatingIpState.AVAILABLE, FloatingIpState.IN_USE],
            terminal_states=[FloatingIpState.ERROR],
            timeout=timeout,
            interval=interval)

    def __repr__(self):
        return "<CB-{0}: {1} ({2})>".format(self.__class__.__name__,
                                            self.id, self.public_ip)

    def __eq__(self, other):
        return (isinstance(other, FloatingIP) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)


class BaseRouter(BaseCloudResource, Router):

    CB_DEFAULT_ROUTER_NAME = os.environ.get('CB_DEFAULT_ROUTER_NAME',
                                            'cloudbridge-router')

    def __init__(self, provider):
        super(BaseRouter, self).__init__(provider)

    def __repr__(self):
        return "<CB-{0}: {1} ({2})>".format(self.__class__.__name__, self.id,
                                            self.name)

    def __eq__(self, other):
        return (isinstance(other, Router) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)


class BaseInternetGateway(BaseCloudResource, BaseObjectLifeCycleMixin,
                          InternetGateway):

    CB_DEFAULT_INET_GATEWAY_NAME = os.environ.get(
        'CB_DEFAULT_INET_GATEWAY_NAME', 'cloudbridge-inetgateway')

    def __init__(self, provider):
        super(BaseInternetGateway, self).__init__(provider)
        self.__provider = provider

    def __repr__(self):
        return "<CB-{0}: {1} ({2})>".format(self.__class__.__name__, self.id,
                                            self.name)

    def __eq__(self, other):
        return (isinstance(other, InternetGateway) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)

    def wait_till_ready(self, timeout=None, interval=None):
        self.wait_for(
            [GatewayState.AVAILABLE],
            terminal_states=[GatewayState.ERROR, GatewayState.UNKNOWN],
            timeout=timeout,
            interval=interval)
