use rhai::{
    Engine,
    EvalAltResult,
};

use crate::bot::Message;
use crate::Action;
use crate::BotAPI;

pub struct MessageAction {
    pub template: String,
}

impl Action for MessageAction {
    fn call(
        &self,
        api: &BotAPI,
        message: &Message,
        rhai_engine: &Engine,
    ) {
        let _ =
            api.send_message(message.chat_id, self.template.as_str(), message.id, 16,);
    }
}
